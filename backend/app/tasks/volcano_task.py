# backend/app/tasks/volcano_task.py
import os
import uuid
import io
import json
import traceback
from typing import Any, Dict
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.orm import Session as SQLAlchemySession

from app.db.session import SessionLocal
from app import crud, models, schemas
from app.core.config import settings
from app.services.s3_service import s3_service
from app.utils.config_loader import load_yaml_config
from app.models.analysis_run import AnalysisStatus

# Import the processor and its Pydantic schema for VOLCANO PLOT
from app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq import volcano_processor
from app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano import VolcanoParams as ToolVolcanoParams

# This is needed to ensure the task is registered with the Celery app
from app.celery_worker import celery_app

@celery_app.task(name="app.celery_worker.run_volcano_plot_analysis", bind=True, max_retries=1, default_retry_delay=30)
def run_volcano_plot_analysis(self, analysis_run_id: str, dataset_s3_path: str, parameters: dict):
    """
    Celery task to run volcano plot analysis, now in its own dedicated module.
    """
    task_log_prefix = f"TASK [ID:{self.request.id}, RunID:{analysis_run_id}]"
    print(f"{task_log_prefix} Received.")

    db: SQLAlchemySession = SessionLocal()
    analysis_run_uuid = uuid.UUID(analysis_run_id)
    db_run: models.AnalysisRun | None = None
    input_file_buffer: io.BytesIO | None = None

    final_status: AnalysisStatus = AnalysisStatus.FAILED
    final_error_message: str | None = "Task did not complete due to an unexpected issue."
    final_run_log_update: str = ""
    output_artifacts: Dict[str, Any] = {}

    try:
        db_run = crud.get_analysis_run(db, analysis_run_id=analysis_run_uuid)
        if not db_run:
            raise ValueError("AnalysisRun record not found in database.")

        crud.update_analysis_run_status(db, db_run=db_run, status=AnalysisStatus.RUNNING)
        db.commit()
        print(f"{task_log_prefix} Status updated to RUNNING.")

        print(f"{task_log_prefix} Downloading input file from S3: {dataset_s3_path}")
        s3_object_key = dataset_s3_path.replace(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/", "", 1)
        input_file_buffer = s3_service.download_file_to_buffer(
            bucket_name=settings.S3_BUCKET_NAME_DATASETS,
            object_key=s3_object_key
        )
        if not input_file_buffer:
            raise ConnectionError("Failed to download input file from S3.")
        print(f"{task_log_prefix} Input file downloaded successfully.")

        print(f"{task_log_prefix} Preparing to run processor.")
        tool_config_yaml_path = "benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.yaml"
        tool_default_config = load_yaml_config(tool_config_yaml_path)
        
        processor_params_obj = ToolVolcanoParams(**parameters)

        class MockFileWithFilename:
            def __init__(self, buffer: io.BytesIO, filename: str):
                self.file = buffer
                self.filename = filename
                self.seek = buffer.seek
                self.read = buffer.read

        original_filename = s3_object_key.split('/')[-1]
        mock_file_obj = MockFileWithFilename(input_file_buffer, original_filename)

        print(f"{task_log_prefix} Executing volcano_processor.run...")
        result_dict = volcano_processor.run(
            file_obj=mock_file_obj,
            params=processor_params_obj,
            config=tool_default_config
        )
        print(f"{task_log_prefix} Processor finished.")

        print(f"{task_log_prefix} Uploading results JSON to S3.")
        results_json_bytes = json.dumps(result_dict, indent=2).encode('utf-8')
        results_json_buffer = io.BytesIO(results_json_bytes)
        
        json_s3_object_name = f"analysis_runs/{analysis_run_id}/results/results.json"
        
        s3_service.s3_client_internal.upload_fileobj(
            results_json_buffer,
            settings.S3_BUCKET_NAME_RESULTS,
            json_s3_object_name
        )
        
        results_json_s3_path = f"s3://{settings.S3_BUCKET_NAME_RESULTS}/{json_s3_object_name}"
        print(f"{task_log_prefix} Results JSON uploaded to: {results_json_s3_path}")

        output_artifacts = {
            "results_json_s3_path": results_json_s3_path,
            "summary_stats": result_dict.get("summary_stats", {})
        }
        final_status = AnalysisStatus.COMPLETED
        final_error_message = None

    except ValueError as ve:
        print(f"{task_log_prefix} ERROR (ValueError): {str(ve)}\n{traceback.format_exc()}")
        final_status = AnalysisStatus.FAILED
        final_error_message = f"Configuration or data error: {str(ve)}"
        output_artifacts = {"error_details": str(ve), "traceback": traceback.format_exc()}
    except Exception as e:
        print(f"{task_log_prefix} ERROR (Exception): {str(e)}\n{traceback.format_exc()}")
        final_error_message = f"An unexpected error occurred: {str(e)}"
        output_artifacts = {"error_details": str(e), "traceback": traceback.format_exc()}
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            print(f"{task_log_prefix} Max retries exceeded.")
            pass
    finally:
        print(f"{task_log_prefix} Finalizing task. Status: {final_status}")
        if db_run:
            crud.update_analysis_run_internal(
                db=db,
                db_run=db_run,
                run_in={
                    "status": final_status,
                    "error_message": final_error_message,
                    "output_artifacts": output_artifacts,
                    "run_log": final_run_log_update
                }
            )
            db.commit()
            print(f"{task_log_prefix} Final status saved to DB.")
        
        if input_file_buffer:
            input_file_buffer.close()

        db.close()
        print(f"{task_log_prefix} Task finished.")