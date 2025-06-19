# backend/app/api/endpoints/volcano_plot_tool_router.py
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db.session import get_db
from app.tasks.volcano_task import run_volcano_plot_analysis as run_volcano_task # Import Celery task
from app.core.config import settings

# Import the placeholder for current user (replace with actual auth later)
from app.api.endpoints.core.project_router import get_current_active_user_placeholder

router = APIRouter()

# Define a Pydantic model for the specific inputs of the volcano plot submission
class VolcanoPlotSubmit(BaseModel):
    project_id: uuid.UUID
    primary_input_dataset_id: uuid.UUID
    analysis_name: Optional[str] = "Volcano Plot Analysis" # Default name for the run
    description: Optional[str] = None
    # --- Tool-specific parameters ---
    # These should align with what your volcano_processor.py expects
    # or what the frontend will send based on volcano.yaml config.
    # For now, let's include the ones from your existing frontend/schemas.
    gene_col: Optional[str] = None
    log2fc_col: Optional[str] = None
    pvalue_col: Optional[str] = None
    fold_change_threshold: Optional[float] = 1.0 # Default from your volcano.yaml
    p_value_threshold: Optional[float] = 0.05    # Default from your volcano.yaml
    # label_top_n: Optional[int] = 0 # Add if you use this


@router.post("/submit", response_model=schemas.AnalysisRunRead, status_code=status.HTTP_202_ACCEPTED)
async def submit_volcano_plot_job(
    *,
    db: Session = Depends(get_db),
    submission_data: VolcanoPlotSubmit, # Use the new Pydantic model for request body
    current_user: models.User = Depends(get_current_active_user_placeholder),
) -> Any:
    """
    Submit a new Volcano Plot analysis job.
    This creates an AnalysisRun record and enqueues a Celery task.
    """
    # 1. Validate input dataset exists and belongs to the project (or user has access)
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
    # Add further authorization checks for project access by current_user if needed

    # 2. Prepare parameters for AnalysisRun and Celery task
    tool_parameters = {
        "gene_col": submission_data.gene_col,
        "log2fc_col": submission_data.log2fc_col,
        "pvalue_col": submission_data.pvalue_col,
        "fold_change_threshold": submission_data.fold_change_threshold,
        "p_value_threshold": submission_data.p_value_threshold,
        # "label_top_n": submission_data.label_top_n,
    }
    # Filter out None values from parameters if your processor prefers that
    tool_parameters_cleaned = {k: v for k, v in tool_parameters.items() if v is not None}

    # 3. Create AnalysisRun Pydantic model for DB creation
    analysis_run_in = schemas.AnalysisRunCreate(
        name=submission_data.analysis_name or f"Volcano Plot on {dataset.name}",
        description=submission_data.description,
        project_id=submission_data.project_id,
        tool_id="benchmate_volcano_plot_v1", # Define a consistent tool ID
        tool_version="1.0.0", # Version your tool
        parameters=tool_parameters_cleaned,
        primary_input_dataset_id=submission_data.primary_input_dataset_id,
    )

    # 4. Create AnalysisRun record in DB
    try:
        db_analysis_run = crud.create_analysis_run(
            db=db, run_in=analysis_run_in, created_by_user_id=current_user.id
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    # 5. Enqueue Celery task
    # Pass necessary information for the task to execute
    try:
        run_volcano_task.delay(
            analysis_run_id=str(db_analysis_run.id), # Pass ID as string
            dataset_s3_path=dataset.file_path_s3, # Get S3 path from Dataset model
            parameters=tool_parameters_cleaned,
            # You might also need to pass user_id if tasks need to impersonate or log as user
        )
    except Exception as e:
        # If enqueuing fails, we should ideally roll back the AnalysisRun creation
        # or mark it as FAILED immediately. For now, simple error.
        # Log error e
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

    return db_analysis_run # Return the created AnalysisRun record (status: PENDING)