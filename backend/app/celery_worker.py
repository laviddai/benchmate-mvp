# backend/app/celery_worker.py
from celery import Celery
import time
import os

# It's common to configure Celery using environment variables,
# especially for broker URL and backend URL.
# These would typically be set in your Docker environment or .env file.

# Example: Using REDIS_URL from environment (or a default for local dev)
# Ensure your .env file (read by core.config) or Docker env vars have REDIS_URL
# For now, we'll hardcode a default that matches our Docker Compose setup for Redis.
# Later, we can integrate this with app.core.config.settings

REDIS_HOSTNAME = os.getenv("REDIS_HOSTNAME", "redis") # 'redis' is the service name in docker-compose
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
CELERY_BROKER_URL = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/1" # Use a different DB for results

# Initialize Celery
# The first argument is the name of the current module, important for Celery's autodiscovery.
# The `broker` argument specifies the URL of the message broker (Redis in our case).
# The `backend` argument specifies the URL of the result backend (also Redis).
celery_app = Celery(
    "benchmate_tasks", # A name for your Celery application/project
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['app.celery_worker'] # List of modules to import when the worker starts (for task discovery)
                                # If tasks are in this file, this module needs to be included.
)

# Optional Celery configuration
celery_app.conf.update(
    task_serializer="json",         # Default serializer
    accept_content=["json"],        # Default content types to accept
    result_serializer="json",       # Default result serializer
    timezone="UTC",                 # Configure timezone
    enable_utc=True,                # Enable UTC
    # task_track_started=True,      # If you want tasks to report 'started' state
    # worker_prefetch_multiplier=1, # Can be useful for long-running tasks to prevent pre-fetching too many
)


# --- Example Task (Placeholder) ---
@celery_app.task(name="app.celery_worker.debug_task") # Explicit name is good practice
def debug_task(x: int, y: int) -> int:
    """A simple task that adds two numbers after a delay."""
    print(f"Debug task started with args: x={x}, y={y}")
    time.sleep(5)  # Simulate some work
    result = x + y
    print(f"Debug task finished. Result: {result}")
    return result

# --- Placeholder for Volcano Plot Task ---
@celery_app.task(name="app.celery_worker.run_volcano_plot_analysis")
def run_volcano_plot_analysis(analysis_run_id: str, dataset_s3_path: str, parameters: dict):
    """
    Placeholder for the actual volcano plot analysis logic.
    This task will:
    1. Update AnalysisRun status to RUNNING.
    2. Download dataset from S3.
    3. Run volcano_processor.py.
    4. Upload results (plot image, summary data) to S3.
    5. Update AnalysisRun status to COMPLETED/FAILED and store result paths/summary.
    """
    from app.db.session import SessionLocal # Import here to avoid circular deps at module level
    from app import crud # Import crud operations
    import uuid

    print(f"Celery Task: Starting volcano plot for AnalysisRun ID: {analysis_run_id}")
    print(f"Dataset S3 Path: {dataset_s3_path}")
    print(f"Parameters: {parameters}")

    db: Session = SessionLocal()
    analysis_run_uuid = uuid.UUID(analysis_run_id)
    db_run = None # Initialize to None

    try:
        # 1. Get the AnalysisRun object and update status to RUNNING
        db_run = crud.get_analysis_run(db, analysis_run_id=analysis_run_uuid)
        if not db_run:
            print(f"Error: AnalysisRun {analysis_run_id} not found in DB.")
            # Optionally, you could try to create a log entry or send an alert
            return {"status": "error", "message": "AnalysisRun not found"}

        # Check if already completed or failed to prevent re-running (idempotency check)
        if db_run.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
             print(f"Info: AnalysisRun {analysis_run_id} already processed with status {db_run.status}. Skipping.")
             return {"status": db_run.status.value, "message": "Already processed."}


        crud.update_analysis_run_status(db=db, db_run=db_run, status=AnalysisStatus.RUNNING)
        print(f"Celery Task: AnalysisRun {analysis_run_id} status updated to RUNNING.")

        # Simulate work for now
        time.sleep(10) # Replace with actual volcano_processor.py logic
        # TODO:
        # - Download dataset_s3_path from S3/MinIO
        # - Run volcano_processor.py with the downloaded file and parameters
        # - Save output plot to S3/MinIO
        # - Prepare output_artifacts dictionary

        # Placeholder results
        output_artifacts_result = {
            "plot_image_s3_path": f"s3://{settings.S3_BUCKET_NAME_RESULTS}/analysis_runs/{analysis_run_id}/volcano_plot.png",
            "summary_stats": {"up_regulated": 100, "down_regulated": 50}
        }
        final_status = AnalysisStatus.COMPLETED
        error_msg = None
        run_log_msg = "Volcano plot analysis completed successfully (simulated)."

    except Exception as e:
        print(f"Celery Task: Error during volcano plot for {analysis_run_id}: {str(e)}")
        # Log the full traceback for debugging
        import traceback
        traceback.print_exc()
        final_status = AnalysisStatus.FAILED
        error_msg = str(e)
        run_log_msg = f"Volcano plot analysis failed: {str(e)}"
        output_artifacts_result = {} # No outputs on failure

    finally:
        if db_run: # Ensure db_run was fetched
            # Update AnalysisRun with final status, outputs, and logs
            # We need to commit changes in a separate session or handle carefully
            # if the original session from the worker is used.
            # For simplicity now, assume this crud function handles its own session or the passed one.
            crud.update_analysis_run_status(db=db, db_run=db_run, status=final_status, error_message=error_msg, run_log_update=f"\n{run_log_msg}")
            if final_status == AnalysisStatus.COMPLETED:
                crud.update_analysis_run_outputs(db=db, db_run=db_run, output_artifacts=output_artifacts_result)
            print(f"Celery Task: AnalysisRun {analysis_run_id} final status updated to {final_status.value}.")
        db.close()

    return {"status": final_status.value, "analysis_run_id": analysis_run_id}

# If you have tasks in other files, e.g., app.tasks.another_module.some_task
# you would add 'app.tasks.another_module' to the `include` list in Celery() constructor.