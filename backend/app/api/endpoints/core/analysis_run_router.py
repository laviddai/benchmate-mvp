# backend/app/api/endpoints/analysis_run_router.py
import uuid
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas # Uses __init__.py for cleaner imports
from app.db.session import get_db

# Import the placeholder for current user (replace with actual auth later)
from app.api.endpoints.core.project_router import get_current_active_user_placeholder

router = APIRouter()


@router.get("/project/{project_id}/", response_model=List[schemas.AnalysisRunRead])
def read_analysis_runs_for_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user_placeholder), # Auth placeholder
) -> Any:
    """
    Retrieve analysis runs for a specific project.
    (Authorization: user must be owner or member of project - to be implemented)
    """
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Basic authorization placeholder:
    # is_owner = project.created_by_user_id == current_user.id
    # is_member = any(member.user_id == current_user.id for member in project.members)
    # if not (is_owner or is_member) and not (current_user.role == "admin"):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions for this project")

    analysis_runs = crud.get_analysis_runs_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return analysis_runs


@router.get("/{analysis_run_id}", response_model=schemas.AnalysisRunRead)
def read_analysis_run_by_id(
    analysis_run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user_placeholder), # Auth placeholder
) -> Any:
    """
    Get a specific analysis run by ID.
    (Authorization: user must have access to the analysis run's project - to be implemented)
    """
    analysis_run = crud.get_analysis_run(db, analysis_run_id=analysis_run_id)
    if not analysis_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found")

    # Basic authorization placeholder for project access:
    # project = analysis_run.project # Assumes project is eager loaded or accessible
    # if project:
    #     is_owner = project.created_by_user_id == current_user.id
    #     is_member = any(member.user_id == current_user.id for member in project.members)
    #     if not (is_owner or is_member) and not (current_user.role == "admin"):
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions for this analysis run's project")
    # else: # Should not happen if FK is enforced and project loaded
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Analysis run is not associated with a project.")

    return analysis_run

# Note:
# - Creation of AnalysisRun records will typically happen as part of submitting a specific analysis job
#   (e.g., via a POST /api/analyses/volcano_plot/submit endpoint).
# - Updating AnalysisRun (status, results) will be done by Celery workers or internal processes,
#   not typically directly by user API calls, except maybe for name/description.
# - Deleting AnalysisRun might be an admin function or user function with appropriate checks.

# Example of how a user might update mutable fields like name/description:
@router.put("/{analysis_run_id}", response_model=schemas.AnalysisRunRead)
def update_user_modifiable_analysis_run_fields(
    analysis_run_id: uuid.UUID,
    run_update_in: schemas.AnalysisRunUserUpdate, # Schema with only user-modifiable fields
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user_placeholder), # Auth placeholder
) -> Any:
    """
    Update user-modifiable fields of an analysis run (e.g., name, description).
    """
    db_run = crud.get_analysis_run(db, analysis_run_id=analysis_run_id)
    if not db_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found")

    # Authorization: Check if current_user is the creator of the run or has project permissions
    if db_run.created_by_user_id != current_user.id and not (current_user.role == "admin"):
         # More granular project role checks could be added here
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to update this analysis run")

    # Use a generic update from CRUD, or create a specific one if needed
    # For this, we'll assume crud_analysis_run.update_analysis_run_internal can handle it
    # by passing a dict from run_update_in.model_dump(exclude_unset=True)
    update_data = run_update_in.model_dump(exclude_unset=True)
    if not update_data:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided")

    # We need a more general update function in crud_analysis_run for this,
    # or adapt update_analysis_run_internal to be more flexible.
    # For now, let's imagine a crud.update_analysis_run function:
    # updated_run = crud.update_analysis_run(db=db, db_run=db_run, run_in=update_data)
    # Placeholder until such a general update function is robustly defined in CRUD:
    for field, value in update_data.items():
        if hasattr(db_run, field): # Make sure the field exists on the model
            setattr(db_run, field, value)
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    updated_run = db_run

    return updated_run