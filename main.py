from celery_worker import analyze_pr_task, celery_app  # <--- ADD , celery_app HERE
from fastapi import FastAPI
from pydantic import BaseModel
from celery.result import AsyncResult
from celery_worker import analyze_pr_task  # Import the task

# Create an instance of the FastAPI application
app = FastAPI()

# 1. Define the request model (what the user sends us)
class PRRequest(BaseModel):
    repo_url: str
    pr_number: int

# 2. Update the root endpoint (this was your test)
@app.get("/")
def read_root():
    """A simple endpoint to check if the API is alive."""
    return {"message": "Hello! The Code Review API is running."}

# 3. Create the "analyze-pr" endpoint
@app.post("/analyze-pr")
def start_analysis(request: PRRequest):
    """
    This endpoint accepts a PR and sends it to the Celery
    worker for analysis. It returns a task ID immediately.
    """
    # This '.delay()' sends the "order" to the "kitchen" (Celery/Redis)
    # and returns *immediately*.
    task = analyze_pr_task.delay(request.repo_url, request.pr_number)
    
    # Return the "receipt number" (task ID) to the user.
    return {"task_id": task.id, "status": "pending"}

# 4. Create the "status" endpoint
@app.get("/status/{task_id}")
def get_task_status(task_id: str):
    """
    This endpoint checks the current status of a task
    (e.g., PENDING, SUCCESS, FAILURE).
    """
    # 'AsyncResult' lets us look up a task in the "results counter" (Redis)
    task_result = AsyncResult(task_id, app=celery_app) # <--- ADD app=celery_app HERE
    
    return {
        "task_id": task_id,
        "status": task_result.status
    }

# 5. Create the "results" endpoint
@app.get("/results/{task_id}")
def get_task_results(task_id: str):
    """
    This endpoint retrieves the final results of a
    completed task.
    """
    # Look up the task in Redis, just like before
    task_result = AsyncResult(task_id, app=celery_app)
    
    # Check if the task is finished
    if not task_result.ready():
        # It's not done, tell the user it's still processing
        return {"task_id": task_id, "status": "processing"}
        
    # Check if the task failed
    if task_result.failed():
        # It failed, return the error message
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(task_result.result)
        }
            
    # If it's ready AND it didn't fail, it must be a success
    # Return the "result" (the dictionary from your placeholder task)
    return {
        "task_id": task_id,
        "status": "completed",
        "results": task_result.result  # This is the important part!
    }