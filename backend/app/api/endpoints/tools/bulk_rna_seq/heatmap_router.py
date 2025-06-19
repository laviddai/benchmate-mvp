# backend/app/api/endpoints/tools/bulk_rna_seq/heatmap_router.py
import uuid
from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app import crud, models, schemas
from app.db.session import get_db
# --- NEW: Import the new Celery task for Heatmap ---
from app.tasks.heatmap_task import run_heatmap_analysis as run_heatmap_task
from app.api.endpoints.core.project_router import get_current_active_user_placeholder

router = APIRouter()

# --- NEW: Pydantic model for Heatmap submission ---
class HeatmapSubmit(BaseModel):
    """Defines the request body for submitting a Heatmap analysis."""
    project_id: uuid.UUID
    primary_input_dataset_id: uuid.UUID
    analysis_name: Optional[str] = Field("Gene Expression Heatmap", description="A custom name for this analysis run.")
    
    # --- Tool-specific parameters ---
    # These match the HeatmapParams in the processor
    gene_selection_method: str = Field("top_n_variable", description="Method to select genes.")
    top_n_genes: int = Field(50, description="Number of genes for top_n_variable.")
    de_logfc_threshold: float = Field(1.0, description="LogFC threshold for DE genes.")
    de_pvalue_threshold: float = Field(0.05, description="P-value/FDR threshold for DE genes.")
    gene_list: Optional[List[str]] = Field(None, description="Specific list of genes to plot.")
    scaling_method: str = Field("z_score_row", description="Data scaling method.")
    cluster_genes: bool = Field(True, description="Whether to cluster genes.")
    cluster_samples: bool = Field(True, description="Whether to cluster samples.")
    clustering_method: str = Field("average", description="Clustering linkage method.")
    distance_metric: str = Field("euclidean", description="Clustering distance metric.")


@router.post("/submit", response_model=schemas.AnalysisRunRead, status_code=status.HTTP_202_ACCEPTED)
async def submit_heatmap_job(
    *,
    db: Session = Depends(get_db),
    submission_data: HeatmapSubmit,
    current_user: models.User = Depends(get_current_active_user_placeholder),
) -> Any:
    """
    Submit a new Heatmap analysis job.
    """
    dataset = crud.get_dataset(db, dataset_id=submission_data.primary_input_dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Input dataset not found.")
    if dataset.project_id != submission_data.project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset does not belong to project.")

    tool_parameters = submission_data.model_dump(exclude={"project_id", "primary_input_dataset_id"})
    
    analysis_run_in = schemas.AnalysisRunCreate(
        name=submission_data.analysis_name,
        project_id=submission_data.project_id,
        tool_id="benchmate_heatmap_v1",
        tool_version="1.0.0",
        parameters=tool_parameters,
        primary_input_dataset_id=submission_data.primary_input_dataset_id,
    )

    db_analysis_run = crud.create_analysis_run(db=db, run_in=analysis_run_in, created_by_user_id=current_user.id)

    try:
        run_heatmap_task.delay(
            analysis_run_id=str(db_analysis_run.id),
            dataset_s3_path=dataset.file_path_s3,
            parameters=tool_parameters,
        )
    except Exception as e:
        crud.update_analysis_run_status(
            db=db, db_run=db_analysis_run, status=models.AnalysisStatus.FAILED,
            error_message=f"Failed to enqueue Celery task: {str(e)}"
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to enqueue analysis task.")

    return db_analysis_run