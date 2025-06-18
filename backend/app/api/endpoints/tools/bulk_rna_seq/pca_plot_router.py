# backend/app/api/endpoints/tools/bulk_rna_seq/pca_plot_router.py
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app import crud, models, schemas
from app.db.session import get_db
from app.celery_worker import run_pca_plot_analysis as run_pca_task
from app.core.config import settings
from app.api.endpoints.core.project_router import get_current_active_user_placeholder

router = APIRouter()

# Pydantic model for PCA submission
class PCASubmit(BaseModel):
    """Defines the request body for submitting a PCA analysis."""
    project_id: uuid.UUID
    primary_input_dataset_id: uuid.UUID
    analysis_name: Optional[str] = Field("PCA Plot Analysis", description="A custom name for this analysis run.")
    
    # Tool-specific parameters that can be passed from the frontend
    grouping_column: Optional[str] = Field(None, description="Column to use for grouping/coloring samples.")
    pc_x_axis: int = Field(1, description="Which principal component to plot on the X-axis.")
    pc_y_axis: int = Field(2, description="Which principal component to plot on the Y-axis.")
    scale_data: bool = Field(True, description="Whether to scale data before PCA.")


@router.post("/submit", response_model=schemas.AnalysisRunRead, status_code=status.HTTP_202_ACCEPTED)
async def submit_pca_plot_job(
    *,
    db: Session = Depends(get_db),
    submission_data: PCASubmit,
    current_user: models.User = Depends(get_current_active_user_placeholder),
) -> Any:
    """
    Submit a new Principal Component Analysis (PCA) job.
    This creates an AnalysisRun record and enqueues a Celery task.
    """
    # 1. Validate input dataset
    dataset = crud.get_dataset(db, dataset_id=submission_data.primary_input_dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Input dataset with ID {submission_data.primary_input_dataset_id} not found."
        )
    if dataset.project_id != submission_data.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input dataset does not belong to the specified project."
        )

    # 2. Prepare parameters for the AnalysisRun record and the Celery task
    tool_parameters = {
        "grouping_column": submission_data.grouping_column,
        "pc_x_axis": submission_data.pc_x_axis,
        "pc_y_axis": submission_data.pc_y_axis,
        "scale_data": submission_data.scale_data,
        "analysis_name": submission_data.analysis_name,
    }
    tool_parameters_cleaned = {k: v for k, v in tool_parameters.items() if v is not None}

    # 3. Create the AnalysisRun record in the database
    analysis_run_in = schemas.AnalysisRunCreate(
        name=submission_data.analysis_name,
        project_id=submission_data.project_id,
        tool_id="benchmate_pca_plot_v1",
        tool_version="1.0.0",
        parameters=tool_parameters_cleaned,
        primary_input_dataset_id=submission_data.primary_input_dataset_id,
    )

    try:
        db_analysis_run = crud.create_analysis_run(
            db=db, run_in=analysis_run_in, created_by_user_id=current_user.id
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    # 4. Enqueue the Celery task
    try:
        run_pca_task.delay(
            analysis_run_id=str(db_analysis_run.id),
            dataset_s3_path=dataset.file_path_s3,
            parameters=tool_parameters_cleaned,
        )
    except Exception as e:
        crud.update_analysis_run_status(
            db=db,
            db_run=db_analysis_run,
            status=models.AnalysisStatus.FAILED,
            error_message=f"Failed to enqueue Celery task: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue analysis task: {str(e)}"
        )

    return db_analysis_run