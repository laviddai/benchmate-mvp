# backend/app/api/endpoints/tools/imaging/filters/gaussian_blur_router.py

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api.endpoints.core.project_router import get_current_active_user_placeholder
from app.db.session import get_db
from app.tasks.imaging_task import run_image_filter_analysis

router = APIRouter()

# --- Pydantic model for submission ---
class GaussianBlurSubmit(BaseModel):
    """Defines the request body for submitting a Gaussian Blur analysis."""
    project_id: uuid.UUID
    primary_input_dataset_id: uuid.UUID
    analysis_name: Optional[str] = Field("Gaussian Blur Filter", description="A custom name for this analysis run.")
    
    # Tool-specific parameters
    sigma: float = Field(..., gt=0, description="Sigma for the Gaussian kernel. Must be positive.")

@router.post("/submit", response_model=schemas.AnalysisRunRead)
def submit_gaussian_blur_analysis(
    *,
    db: Session = Depends(get_db),
    submission_data: GaussianBlurSubmit,
    current_user: models.User = Depends(get_current_active_user_placeholder),
):
    """
    Submit a new Gaussian Blur filter job.
    This creates an AnalysisRun record and enqueues a Celery task.
    """
    # 1. Validate input dataset exists and user has access (basic check)
    dataset = crud.get_dataset(db, dataset_id=submission_data.primary_input_dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Input dataset not found.")
    
    # TODO: Add more robust authorization to check if user is member of dataset.project_id

    # 2. Prepare parameters for AnalysisRun and Celery task
    tool_parameters = {"sigma": submission_data.sigma}

    # 3. Create AnalysisRun record in the database
    analysis_run_in = schemas.AnalysisRunCreate(
        name=submission_data.analysis_name,
        project_id=submission_data.project_id,
        tool_id="benchmate_gaussian_blur_v1", # From our YAML config
        tool_version="1.0.0",
        parameters=tool_parameters,
        primary_input_dataset_id=submission_data.primary_input_dataset_id,
    )
    db_analysis_run = crud.create_analysis_run(
        db=db, run_in=analysis_run_in, created_by_user_id=current_user.id
    )

    # 4. Enqueue the Celery task
    try:
        run_image_filter_analysis.delay(
            analysis_run_id=str(db_analysis_run.id),
            dataset_s3_path=dataset.file_path_s3,
            parameters=tool_parameters,
        )
    except Exception as e:
        # If enqueuing fails, mark the run as FAILED immediately.
        crud.update_analysis_run_status(db, db_run=db_analysis_run, status=AnalysisStatus.FAILED, error_message=f"Failed to enqueue Celery task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit analysis job to the processing queue."
        )

    return db_analysis_run