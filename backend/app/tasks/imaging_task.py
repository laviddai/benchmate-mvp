# backend/app/tasks/imaging_task.py

import io
import json
import logging
import traceback
import uuid
from typing import Any, Dict

from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session as SQLAlchemySession

from app import crud, models, schemas
from app.celery_worker import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.analysis_run import AnalysisStatus
from app.services import s3_service
from app.services.imagej_service import imagej_service

# --- Filter-related imports ---
from app.utils.benchtop.biology.imaging.filters.gaussian_blur_processor import (
    run as gaussian_blur_processor,
)
from app.schemas.benchtop.biology.imaging.filters.gaussian_blur_schema import GaussianBlurParams

# --- NEW: Segmentation-related imports ---
from app.utils.benchtop.biology.imaging.segmentation.auto_threshold_processor import (
    run as auto_threshold_processor,
)
from app.schemas.benchtop.biology.imaging.segmentation.auto_threshold_schema import AutoThresholdParams


# Configure a logger for this task module
logger = get_task_logger(__name__)


@celery_app.task(name="app.tasks.run_image_filter_analysis", bind=True, max_retries=1, default_retry_delay=30)
def run_image_filter_analysis(self, analysis_run_id: str, dataset_s3_path: str, parameters: dict):
    """
    Celery task to run a generic image filter analysis (e.g., Gaussian Blur).
    """
    task_log_prefix = f"TASK [ID:{self.request.id}, RunID:{analysis_run_id}, Tool:Image Filter]"
    logger.info(f"{task_log_prefix}] - Task started.")

    db: SQLAlchemySession = SessionLocal()
    analysis_run_uuid = uuid.UUID(analysis_run_id)
    db_run: models.AnalysisRun | None = None
    
    final_status: AnalysisStatus = AnalysisStatus.FAILED
    final_error_message: str | None = "Task did not complete due to an unexpected issue."
    output_artifacts: Dict[str, Any] = {}

    try:
        db_run = crud.get_analysis_run(db, analysis_run_id=analysis_run_uuid)
        if not db_run:
            raise ValueError("AnalysisRun not found in the database.")

        crud.update_analysis_run_status(db, db_run=db_run, status=AnalysisStatus.RUNNING)
        logger.info(f"{task_log_prefix} - Status updated to RUNNING.")

        s3_object_key = dataset_s3_path.replace(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/", "", 1)
        input_file_buffer = s3_service.download_file_to_buffer(
            bucket_name=settings.S3_BUCKET_NAME_DATASETS, object_key=s3_object_key
        )
        if not input_file_buffer:
            raise FileNotFoundError(f"Could not download input file from S3 path: {dataset_s3_path}")
        logger.info(f"{task_log_prefix} - Successfully downloaded input image from S3.")

        ij_gateway = imagej_service.instance()
        logger.info(f"{task_log_prefix} - Acquired ImageJ gateway instance.")

        processor_params_obj = GaussianBlurParams(**parameters)
        
        result_dict = gaussian_blur_processor(
            ij_gateway=ij_gateway, image_bytes=input_file_buffer.getvalue(), params=processor_params_obj
        )
        logger.info(f"{task_log_prefix} - Image processing completed.")

        processed_image_bytes = result_dict.get("processed_image_bytes")
        if not processed_image_bytes:
            raise ValueError("Processor did not return processed image bytes.")

        image_s3_object_name = f"analysis_runs/{analysis_run_id}/results/filtered_image.png"
        s3_service.upload_file(
            bucket_name=settings.S3_BUCKET_NAME_RESULTS,
            file_obj=io.BytesIO(processed_image_bytes),
            object_name=image_s3_object_name
        )
        image_s3_path = f"s3://{settings.S3_BUCKET_NAME_RESULTS}/{image_s3_object_name}"
        logger.info(f"{task_log_prefix} - Successfully uploaded filtered image to S3 at {image_s3_path}")

        output_artifacts = {
            "filtered_image_s3_path": image_s3_path,
            "summary": result_dict.get("summary", {})
        }
        final_status = AnalysisStatus.COMPLETED
        final_error_message = None

    except Exception as e:
        logger.error(f"{task_log_prefix} - An error occurred: {str(e)}", exc_info=True)
        final_status = AnalysisStatus.FAILED
        final_error_message = f"An unexpected error occurred: {str(e)}"
        output_artifacts = {"error_details": str(e), "traceback": traceback.format_exc()}

    finally:
        if db_run:
            crud.update_analysis_run_internal(
                db=db, db_run=db_run,
                run_in={"status": final_status, "error_message": final_error_message, "output_artifacts": output_artifacts}
            )
            logger.info(f"{task_log_prefix} - Final status '{final_status.value}' updated in DB.")
        db.close()
        logger.info(f"{task_log_prefix} - Task finished.")


# --- NEW TASK FOR AUTO THRESHOLD ---
@celery_app.task(name="app.tasks.run_image_segmentation_analysis", bind=True, max_retries=1, default_retry_delay=30)
def run_image_segmentation_analysis(self, analysis_run_id: str, dataset_s3_path: str, parameters: dict):
    """
    Celery task to run a generic image segmentation analysis (e.g., Auto Threshold).
    This task follows the same robust pattern as the filter analysis task.
    """
    task_log_prefix = f"TASK [ID:{self.request.id}, RunID:{analysis_run_id}, Tool:Image Segmentation]"
    logger.info(f"{task_log_prefix}] - Task started.")

    db: SQLAlchemySession = SessionLocal()
    analysis_run_uuid = uuid.UUID(analysis_run_id)
    db_run: models.AnalysisRun | None = None
    
    final_status: AnalysisStatus = AnalysisStatus.FAILED
    final_error_message: str | None = "Task did not complete due to an unexpected issue."
    output_artifacts: Dict[str, Any] = {}

    try:
        db_run = crud.get_analysis_run(db, analysis_run_id=analysis_run_uuid)
        if not db_run:
            raise ValueError("AnalysisRun not found in the database.")

        crud.update_analysis_run_status(db, db_run=db_run, status=AnalysisStatus.RUNNING)
        logger.info(f"{task_log_prefix} - Status updated to RUNNING.")

        s3_object_key = dataset_s3_path.replace(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/", "", 1)
        input_file_buffer = s3_service.download_file_to_buffer(
            bucket_name=settings.S3_BUCKET_NAME_DATASETS, object_key=s3_object_key
        )
        if not input_file_buffer:
            raise FileNotFoundError(f"Could not download input file from S3 path: {dataset_s3_path}")
        logger.info(f"{task_log_prefix} - Successfully downloaded input image from S3.")

        ij_gateway = imagej_service.instance()
        logger.info(f"{task_log_prefix} - Acquired ImageJ gateway instance.")

        # Validate parameters using the AutoThresholdParams schema
        processor_params_obj = AutoThresholdParams(**parameters)
        
        # Call the auto_threshold_processor
        result_dict = auto_threshold_processor(
            ij_gateway=ij_gateway, image_bytes=input_file_buffer.getvalue(), params=processor_params_obj
        )
        logger.info(f"{task_log_prefix} - Image processing completed.")

        processed_image_bytes = result_dict.get("processed_image_bytes")
        if not processed_image_bytes:
            raise ValueError("Processor did not return processed image bytes.")

        # Save the result with a descriptive name
        image_s3_object_name = f"analysis_runs/{analysis_run_id}/results/thresholded_image.png"
        s3_service.upload_file(
            bucket_name=settings.S3_BUCKET_NAME_RESULTS,
            file_obj=io.BytesIO(processed_image_bytes),
            object_name=image_s3_object_name
        )
        image_s3_path = f"s3://{settings.S3_BUCKET_NAME_RESULTS}/{image_s3_object_name}"
        logger.info(f"{task_log_prefix} - Successfully uploaded thresholded image to S3 at {image_s3_path}")

        output_artifacts = {
            "thresholded_image_s3_path": image_s3_path, # Use a specific key for this output
            "summary": result_dict.get("summary", {})
        }
        final_status = AnalysisStatus.COMPLETED
        final_error_message = None

    except Exception as e:
        logger.error(f"{task_log_prefix} - An error occurred: {str(e)}", exc_info=True)
        final_status = AnalysisStatus.FAILED
        final_error_message = f"An unexpected error occurred: {str(e)}"
        output_artifacts = {"error_details": str(e), "traceback": traceback.format_exc()}

    finally:
        if db_run:
            crud.update_analysis_run_internal(
                db=db, db_run=db_run,
                run_in={"status": final_status, "error_message": final_error_message, "output_artifacts": output_artifacts}
            )
            logger.info(f"{task_log_prefix} - Final status '{final_status.value}' updated in DB.")
        db.close()
        logger.info(f"{task_log_prefix} - Task finished.")