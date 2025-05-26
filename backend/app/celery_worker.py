# backend/app/celery_worker.py
from celery import Celery
import time
import os
import uuid
from datetime import datetime
import io # For BytesIO
import base64 # For decoding plot image
import traceback # For detailed error logging

# Import necessary application components
from app.db.session import SessionLocal, SQLAlchemySession # Explicitly import Session type
from app import crud, models, schemas
from app.models.analysis_run import AnalysisStatus
from app.core.config import settings
from app.services import s3_service

# --- Celery app initialization (remains the same) ---
REDIS_HOSTNAME = os.getenv("REDIS_HOSTNAME", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
CELERY_BROKER_URL = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/1"

celery_app = Celery(
    "benchmate_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['app.celery_worker']
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
# --- End Celery app initialization ---


@celery_app.task(name="app.celery_worker.debug_task")
def debug_task(x: int, y: int) -> int:
    # ... (remains the same) ...
    print(f"Debug task started with args: x={x}, y={y}")
    time.sleep(5)
    result = x + y
    print(f"Debug task finished. Result: {result}")
    return result


# --- MODIFIED Volcano Plot Task ---
@celery_app.task(name="app.celery_worker.run_volcano_plot_analysis", bind=True, max_retries=1, default_retry_delay=30) # Reduced retries for quicker failure feedback during dev
def run_volcano_plot_analysis(self, analysis_run_id: str, dataset_s3_path: str, parameters: dict):
    task_log_prefix = f"TASK [ID:{self.request.id}, RunID:{analysis_run_id}]"
    print(f"{task_log_prefix} STARTED. Dataset: {dataset_s3_path}, Params: {parameters}")

    db: SQLAlchemySession = SessionLocal()
    analysis_run_uuid = uuid.UUID(analysis_run_id)
    db_run: Optional[models.AnalysisRun] = None
    input_file_buffer: Optional[io.BytesIO] = None
    final_status: AnalysisStatus = AnalysisStatus.FAILED # Default to FAILED
    final_error_message: Optional[str] = "Task did not complete due to an unexpected issue."
    final_run_log_update: str = ""
    output_artifacts: Dict[str, Any] = {}

    try:
        db_run = crud.get_analysis_run(db, analysis_run_id=analysis_run_uuid)
        if not db_run:
            print(f"{task_log_prefix} ERROR: AnalysisRun not found. Aborting.")
            # No DB record to update status on, task effectively fails silently from DB perspective
            return {"status": "error", "message": "AnalysisRun not found, cannot proceed."}

        if db_run.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
            print(f"{task_log_prefix} INFO: Already in terminal state {db_run.status}. Skipping.")
            return {"status": db_run.status.value, "analysis_run_id": analysis_run_id, "message": "Already processed."}

        crud.update_analysis_run_status(db=db, db_run=db_run, status=AnalysisStatus.RUNNING)
        final_run_log_update += "\nStatus: RUNNING. Starting analysis."
        print(f"{task_log_prefix} INFO: Status set to RUNNING.")

        # 1. Download input dataset from S3/MinIO
        print(f"{task_log_prefix} INFO: Downloading dataset from {dataset_s3_path}")
        if not dataset_s3_path or not dataset_s3_path.startswith(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/"):
            raise ValueError(f"Invalid S3 path format or wrong bucket for dataset: {dataset_s3_path}")
        
        s3_object_key = dataset_s3_path.replace(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/", "", 1)
        input_file_buffer = s3_service.download_file_to_buffer(
            bucket_name=settings.S3_BUCKET_NAME_DATASETS, object_key=s3_object_key
        )
        if not input_file_buffer:
            raise Exception(f"Failed to download dataset '{s3_object_key}' from S3.")
        final_run_log_update += f"\nDataset '{s3_object_key}' downloaded."
        print(f"{task_log_prefix} INFO: Dataset '{s3_object_key}' downloaded.")

        # 2. Prepare for and run the volcano_processor
        from app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq import volcano_processor
        from app.utils.config_loader import load_yaml_config
        from app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano import VolcanoParams as ToolVolcanoParams

        tool_config_yaml_path = "benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.yaml"
        tool_default_config = load_yaml_config(tool_config_yaml_path)
        
        # The 'parameters' dict from the API should contain keys like 'gene_col', 'log2fc_col', etc.
        # These are used to instantiate the tool-specific Pydantic schema.
        processor_params_obj = ToolVolcanoParams(**parameters)
        final_run_log_update += f"\nUsing parameters: {processor_params_obj.model_dump_json()}"
        print(f"{task_log_prefix} INFO: Running volcano_processor with params: {processor_params_obj.model_dump()}")

        # Create a mock file object that volcano_processor.run can use
        # (as it expects an object with .file and .filename attributes)
        class MockFileWithFilename:
            def __init__(self, buffer: io.BytesIO, filename: str):
                self.file = buffer
                self.filename = filename # Used by processor to infer extension
        
        original_filename = s3_object_key.split('/')[-1] # Get filename from S3 key
        mock_file_obj = MockFileWithFilename(input_file_buffer, original_filename)

        # Execute the processing function
        result_dict = volcano_processor.run(
            file_obj=mock_file_obj,
            params=processor_params_obj,
            config=tool_default_config
        )
        final_run_log_update += f"\nProcessor run complete. Summary: {result_dict.get('summary')}"
        print(f"{task_log_prefix} INFO: Volcano plot processing complete. Summary: {result_dict.get('summary')}")

        # 3. Upload output plot to S3/MinIO
        plot_base64 = result_dict.get("plot_image")
        if not plot_base64 or not plot_base64.startswith("data:image/png;base64,"):
            raise ValueError("Volcano processor did not return a valid base64 PNG plot image.")

        image_data_base64_string = plot_base64.split(",")[1]
        image_bytes = base64.b64decode(image_data_base64_string)
        
        # Use an in-memory buffer to upload the image bytes
        plot_image_buffer = io.BytesIO(image_bytes)
        plot_s3_object_name = f"analysis_runs/{analysis_run_id}/results/volcano_plot.png" # Define a unique S3 key

        # Re-using s3_service.s3_client.upload_fileobj as it's straightforward for BytesIO
        s3_service.s3_client.upload_fileobj(
            plot_image_buffer,
            settings.S3_BUCKET_NAME_RESULTS, # Target bucket for results
            plot_s3_object_name
        )
        plot_image_s3_path = f"s3://{settings.S3_BUCKET_NAME_RESULTS}/{plot_s3_object_name}"
        final_run_log_update += f"\nPlot image uploaded to: {plot_image_s3_path}"
        print(f"{task_log_prefix} INFO: Plot image uploaded to S3: {plot_image_s3_path}")

        output_artifacts = {
            "plot_image_s3_path": plot_image_s3_path,
            "summary_stats": result_dict.get("summary", {}),
        }
        final_status = AnalysisStatus.COMPLETED
        final_error_message = None # Clear any default error message on success
        final_run_log_update += "\nAnalysis successfully completed."

    except ValueError as ve: # Catch specific configuration/data errors
        print(f"{task_log_prefix} ERROR (ValueError): {str(ve)}\n{traceback.format_exc()}")
        final_run_log_update += f"\nERROR (ValueError): {str(ve)}"
        final_status = AnalysisStatus.FAILED
        final_error_message = f"Configuration or data error: {str(ve)}"
        output_artifacts = {"error_details": str(ve), "traceback": traceback.format_exc()}
    except Exception as e: # Catch all other exceptions
        print(f"{task_log_prefix} ERROR (Exception): {str(e)}\n{traceback.format_exc()}")
        final_run_log_update += f"\nERROR (Exception): {str(e)}\n{traceback.format_exc()}"
        final_status = AnalysisStatus.FAILED
        final_error_message = f"An unexpected error occurred: {str(e)}"
        output_artifacts = {"error_details": str(e), "traceback": traceback.format_exc()}
        # For critical, unexpected errors, you might want Celery to retry if configured
        # try:
        #     self.retry(exc=e)
        # except MaxRetriesExceededError:
        #     print(f"{task_log_prefix} Max retries exceeded.")
        #     pass # Will proceed to finally block with FAILED status

    finally:
        if db_run: # Ensure db_run was fetched successfully
            print(f"{task_log_prefix} INFO: Updating final status to {final_status.value}")
            crud.update_analysis_run_status(
                db=db,
                db_run=db_run,
                status=final_status,
                error_message=final_error_message,
                run_log_update=final_run_log_update # Append the accumulated log
            )
            if final_status == AnalysisStatus.COMPLETED:
                crud.update_analysis_run_outputs(db=db, db_run=db_run, output_artifacts=output_artifacts)
        
        if input_file_buffer:
            input_file_buffer.close()
        # plot_image_buffer is local to the try block, will be garbage collected.
        db.close()
        print(f"{task_log_prefix} FINISHED with status: {final_status.value}")

    return {"status": final_status.value, "analysis_run_id": analysis_run_id, "outputs": output_artifacts}