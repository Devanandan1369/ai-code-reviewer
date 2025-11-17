import pytest
import requests_mock
from reviewer import get_pr_diff

# --- Test 1: The "Happy Path" (Successful API Call) ---

def test_get_pr_diff_success(requests_mock):
    """
    Tests if the function correctly returns the diff text
    when the GitHub API call is successful (200 OK).
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 1
    api_url = "https://api.github.com/repos/test/repo/pulls/1"
    
    # 1. Define the "fake" response we want requests_mock to send
    fake_diff_text = "diff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n-print('hello')\n+print('world')"
    
    # 2. Tell requests_mock to "intercept" any GET request to this URL...
    #    ...and return our fake diff text with a 200 OK status.
    requests_mock.get(api_url, text=fake_diff_text, status_code=200)
    
    # 3. Call the actual function we are testing
    result = get_pr_diff(repo_url, pr_number)
    
    # 4. Assert (check) that the result is *exactly* what we expected
    assert result == fake_diff_text

# --- Test 2: The "Failure Path" (404 Not Found) ---

def test_get_pr_diff_not_found(requests_mock):
    """
    Tests if the function correctly returns an error message
    when the GitHub API returns a 404 Not Found error.
    """
    repo_url = "https://github.com/test/repo"
    pr_number = 404
    api_url = "https://api.github.com/repos/test/repo/pulls/404"
    
    # 1. Define the fake error response from GitHub
    fake_error_json = {"message": "Not Found"}
    
    # 2. Tell requests_mock to intercept this URL...
    #    ...and return our fake JSON with a 404 status.
    requests_mock.get(api_url, json=fake_error_json, status_code=404)
    
    # 3. Call the function
    result = get_pr_diff(repo_url, pr_number)
    
    # 4. Assert that the result is the specific ERROR string we expect
    assert result.startswith("ERROR: Pull Request not found")

# --- Test 3: The "Bad Input" Path ---

def test_get_pr_diff_invalid_url():
    """
    Tests if the function returns an error for a malformed repo_url.
    """
    # This URL is missing "github.com/"
    invalid_url = "https://gitlab.com/test/repo"
    
    result = get_pr_diff(invalid_url, 1)
    
    assert result == "ERROR: Invalid repo_url format. Expected 'https://github.com/user/repo'."