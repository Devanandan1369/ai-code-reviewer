import os  # <-- ADD THIS
from dotenv import load_dotenv
load_dotenv()  # This line loads the .env file
from celery import Celery
import time

# --- Import your new "brain" functions ---
from reviewer import get_pr_diff, analyze_code_with_ai

# --- 1. Define the Celery application ---
# Get the Redis URL from environment variables,
# default to localhost if not found (for local development).
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# --- 2. Define the *REAL* "recipe" (the task) ---
@celery_app.task(name="tasks.analyze_pr")
def analyze_pr_task(repo_url, pr_number):
    """
    The main asynchronous task to analyze a pull request.
    """
    
    print(f"TASK RECEIVED: Analyzing {repo_url}, PR #{pr_number}")

    # --- Step 1: Fetch the "ingredients" (the code diff) ---
    print("STEP 1: Fetching diff from GitHub...")
    diff_text = get_pr_diff(repo_url, pr_number)
    
    # Check if fetching the diff failed
    if diff_text.startswith("ERROR:"):
        print(f"STEP 1 FAILED: {diff_text}")
        # Raise an exception to mark the task as FAILED in Celery
        raise Exception(diff_text)

    print("STEP 1 SUCCESS: Diff fetched.")

    # --- Step 2: "Cook" the ingredients (call the AI brain) ---
    print("STEP 2: Analyzing code with AI...")
    
    # Send the diff text to your AI brain
    analysis_result = analyze_code_with_ai(diff_text)
    
    # Check if the AI analysis failed
    if "error" in analysis_result:
        print(f"STEP 2 FAILED: {analysis_result['error']}")
        # Raise an exception to mark the task as FAILED in Celery
        raise Exception(analysis_result['error'])
    
    print("STEP 2 SUCCESS: AI analysis complete.")
    
    # --- Step 3: Return the final, successful result ---
    # We return the AI's JSON analysis directly, as requested
    return analysis_result