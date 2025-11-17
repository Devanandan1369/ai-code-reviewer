import json
import os
import requests
from litellm import completion

def get_pr_diff(repo_url: str, pr_number: int) -> str:
    """
Fetches the 'diff' (the code changes) for a specific pull request.
    """
    
    # 1. Convert the normal GitHub URL into an API URL
    # Example: "https://github.com/user/repo" -> "user/repo"
    try:
        owner_repo = repo_url.split("github.com/")[1]
    except IndexError:
        return "ERROR: Invalid repo_url format. Expected 'https://github.com/user/repo'."

    # This is the special API address for pull requests
    api_url = f"https://api.github.com/repos/{owner_repo}/pulls/{pr_number}"

    # 2. Set up the required headers for the GitHub API
    # This header tells GitHub we want the 'diff' format
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # 3. Optional: Use a GitHub Token if one is provided
    # This helps you avoid rate limits and access private repos.
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    # 4. Make the web request to GitHub
    try:
        response = requests.get(api_url, headers=headers)
        
        # If the request failed (e.g., 404 Not Found), raise an error
        response.raise_for_status()
        
        # 5. Return the code (as text) if the request was successful
        return response.text
        
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return f"ERROR: Pull Request not found. Check repo_url and pr_number. (URL: {api_url})"
        return f"ERROR: HTTP error occurred: {http_err} (URL: {api_url})"
    except Exception as e:
        return f"ERROR: An unexpected error occurred: {e}"

# This is the "instruction manual" for the AI.
SYSTEM_PROMPT = """
You are an expert, autonomous AI code reviewer.
You will be given a 'git diff' as input.
Your task is to analyze this diff and provide code review feedback.

Analyze the code for:
- Code style and formatting issues
- Potential bugs or errors
- Performance improvements
- Security vulnerabilities
- Best practices

You MUST respond ONLY with a JSON object in the following format.
Do not write *any* other text before or after the JSON.

{
    "files": [
        {
            "name": "path/to/file.py",
            "issues": [
                {
                    "type": "bug",
                    "line": 15,
                    "description": "A clear description of the potential bug.",
                    "suggestion": "A clear suggestion for how to fix the bug."
                },
                {
                    "type": "style",
                    "line": 23,
                    "description": "Line is too long.",
                    "suggestion": "Break the line into multiple lines."
                }
            ]
        }
    ],
    "summary": {
        "total_files": 1,
        "total_issues": 2,
        "critical_issues": 1
    }
}

If you find no issues in a file, you can either omit the file or return an empty "issues" list for it.
If you find no issues at all, return a JSON with an empty "files" list.
"""

def analyze_code_with_ai(diff_text: str) -> dict:
    """
    Analyzes the code diff using the Groq LLaMA model.
    """
    try:
        # 1. Check for the correct Groq key
        if not os.environ.get("GROQ_API_KEY"):
            return {"error": "GROQ_API_KEY environment variable not set."}

        # 2. Set up the messages for the AI
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": diff_text}
        ]

        # 3. Call the AI using LiteLLM
        response = completion(
            model="groq/llama-3.1-8b-instant",
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        # 4. Extract the AI's response
        ai_response_text = response.choices[0].message.content
        
        # 5. Convert the JSON string into a Python dictionary and return it
        return json.loads(ai_response_text)
        
    except json.JSONDecodeError:
        return {"error": "AI response was not valid JSON.", "ai_response": ai_response_text}
    except Exception as e:
        return {"error": f"An error occurred during AI analysis: {e}"}