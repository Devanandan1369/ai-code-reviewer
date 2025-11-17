import streamlit as st
import requests
import time
import os  # <-- ADD THIS IMPORT

# --- Configuration ---
# This is the address of your FastAPI server
# Use an environment variable, but default to localhost for local testing
API_BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000") # <-- THIS IS THE CHANGED LINE

# --- Helper Functions ---

def start_analysis(repo_url, pr_number):
    """
    Sends a POST request to the FastAPI /analyze-pr endpoint
    to start a new analysis task.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze-pr",
            json={"repo_url": repo_url, "pr_number": pr_number}
        )
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error starting analysis: {e}")
        return None

def get_task_status(task_id):
    """
    Sends a GET request to the /status/<task_id> endpoint
    to check if the task is finished.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/status/{task_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error checking status: {e}")
        return None

def get_task_results(task_id):
    """
    Sends a GET request to the /results/<task_id> endpoint
    to get the final analysis data.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/results/{task_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting results: {e}")
        return None

# --- Streamlit UI ---

st.set_page_config(page_title="AI Code Reviewer", layout="wide")
st.title("🤖 Autonomous AI Code Review Agent")
st.write("Enter a GitHub PR to analyze. This app will send a request to the FastAPI backend, which uses Celery and an LLM to review the code.")

# Use session state to remember the task ID and results
if 'task_id' not in st.session_state:
    st.session_state.task_id = None
if 'results' not in st.session_state:
    st.session_state.results = None

# --- Input Form ---
with st.form("pr_form"):
    st.write("Enter Pull Request Details")
    
    # Example URL pre-filled for easy testing
    repo_url_input = st.text_input(
        "Repository URL", 
        "https://github.com/twbs/bootstrap"
    )
    
    # Example PR pre-filled
    pr_number_input = st.number_input(
        "Pull Request Number", 
        min_value=1, 
        value=41867,
        step=1
    )
    
    submitted = st.form_submit_button("Start Analysis")

# --- Form Submission Logic ---
if submitted:
    if repo_url_input and pr_number_input:
        st.session_state.task_id = None  # Clear old results
        st.session_state.results = None  # Clear old results
        
        with st.spinner("Submitting task to backend..."):
            start_response = start_analysis(repo_url_input, int(pr_number_input))
        
        if start_response and "task_id" in start_response:
            st.session_state.task_id = start_response["task_id"]
            st.success(f"Task submitted successfully! Task ID: `{st.session_state.task_id}`")
            st.info("Now polling for results... The page will update automatically.")
        else:
            st.error("Failed to submit task. See error above.")

# --- Polling and Results Display ---
if st.session_state.task_id:
    
    # Show a "Check Again" button to manually refresh
    st.button("🔄 Check Status Again")
    
    try:
        with st.spinner(f"Waiting for task `{st.session_state.task_id}` to complete..."):
            while True:
                status_response = get_task_status(st.session_state.task_id)
                
                if not status_response:
                    st.error("Failed to get task status.")
                    break

                status = status_response.get("status")
                
                if status == "SUCCESS" or status == "completed":
                    st.success("Task completed!")
                    break
                elif status == "FAILURE" or status == "failed":
                    st.error("Task failed!")
                    results_response = get_task_results(st.session_state.task_id)
                    st.session_state.results = results_response
                    break
                
                # Wait 2 seconds before checking again
                time.sleep(2)
        
        # --- Display Final Results ---
        if st.session_state.results is None: # Only fetch if we don't have them
            results_response = get_task_results(st.session_state.task_id)
            st.session_state.results = results_response
            
        if st.session_state.results:
            st.header("Analysis Results")
            
            # Show the raw JSON in an expandable box
            with st.expander("Show Raw JSON Response", expanded=False):
                st.json(st.session_state.results)

            # Display the formatted results
            if st.session_state.results.get("status") == "completed":
                analysis = st.session_state.results.get("results", {})
                
                # Display Summary
                summary = analysis.get("summary")
                if summary:
                    st.subheader("Analysis Summary")
                    cols = st.columns(3)
                    cols[0].metric("Total Files Analyzed", summary.get("total_files", 0))
                    cols[1].metric("Total Issues Found", summary.get("total_issues", 0))
                    cols[2].metric("Critical Issues", summary.get("critical_issues", 0))
                
                # Display Files and Issues
                files = analysis.get("files", [])
                if files:
                    st.subheader("Files Analyzed")
                    for file in files:
                        st.markdown(f"#### 📄 `{file.get('name')}`")
                        issues = file.get("issues", [])
                        if not issues:
                            st.success("No issues found in this file.")
                            continue
                        
                        for issue in issues:
                            st.warning(f"**{issue.get('type', 'ISSUE').upper()}** on line **{issue.get('line')}**")
                            st.markdown(f"> **Description:** {issue.get('description')}")
                            st.markdown(f"> **Suggestion:** {issue.get('suggestion')}")
                            st.divider()
                else:
                    st.success("🎉 No issues found in any files!")
                    
            elif st.session_state.results.get("status") == "failed":
                st.error(f"Task Failed: {st.session_state.results.get('error')}")

    except Exception as e:
        st.error(f"An error occurred while fetching results: {e}")