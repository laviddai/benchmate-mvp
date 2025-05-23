# backend/app/crud/crud_analysis_run.py
import uuid
from typing import Any, Dict, Optional, Union, List
from datetime import datetime

from sqlalchemy.orm import Session, selectinload

from app.models.analysis_run import AnalysisRun, AnalysisStatus
from app.models.project import Project # For type checking if needed
from app.models.user import User     # For type checking if needed
from app.schemas.analysis_run_schema import AnalysisRunCreate, AnalysisRunUpdateInternal

def get_analysis_run(db: Session, analysis_run_id: uuid.UUID) -> Optional[AnalysisRun]:
    """
    Retrieve a single analysis run by its ID.
    Optionally eager load relationships.
    """
    return (
        db.query(AnalysisRun)
        .options(
            selectinload(AnalysisRun.project),
            selectinload(AnalysisRun.creator),
            selectinload(AnalysisRun.primary_input_dataset)
        )
        .filter(AnalysisRun.id == analysis_run_id)
        .first()
    )

def get_analysis_runs_by_project(
    db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[AnalysisRun]:
    """
    Retrieve analysis runs belonging to a specific project with pagination.
    """
    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.project_id == project_id)
        .options(selectinload(AnalysisRun.creator), selectinload(AnalysisRun.primary_input_dataset))
        .order_by(AnalysisRun.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_analysis_runs_by_user(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[AnalysisRun]:
    """
    Retrieve analysis runs created by a specific user with pagination.
    """
    return (
        db.query(AnalysisRun)
        .filter(AnalysisRun.created_by_user_id == user_id)
        .options(selectinload(AnalysisRun.project), selectinload(AnalysisRun.primary_input_dataset))
        .order_by(AnalysisRun.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_analysis_run(
    db: Session, *, run_in: AnalysisRunCreate, created_by_user_id: uuid.UUID
) -> AnalysisRun:
    """
    Create a new analysis run record.
    Typically called when a new analysis job is submitted.
    """
    # Ensure project and user exist (optional, could be caught by FK constraints too)
    project = db.query(Project).filter(Project.id == run_in.project_id).first()
    if not project:
        raise ValueError(f"Project with id {run_in.project_id} not found.")

    creator = db.query(User).filter(User.id == created_by_user_id).first()
    if not creator:
        raise ValueError(f"User with id {created_by_user_id} not found.")

    # Ensure primary_input_dataset exists if provided
    if run_in.primary_input_dataset_id:
        from app.models.dataset import Dataset # Local import to avoid circularity if needed
        dataset = db.query(Dataset).filter(Dataset.id == run_in.primary_input_dataset_id).first()
        if not dataset:
            raise ValueError(f"Primary input dataset with id {run_in.primary_input_dataset_id} not found.")


    db_run_data = run_in.model_dump(exclude_unset=True)
    db_run = AnalysisRun(
        **db_run_data,
        created_by_user_id=created_by_user_id,
        status=AnalysisStatus.PENDING, # Default initial status
        queued_at=datetime.utcnow() # Set queued time
    )

    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

def update_analysis_run_status( # A specific update function for status
    db: Session,
    *,
    db_run: AnalysisRun,
    status: AnalysisStatus,
    error_message: Optional[str] = None,
    run_log_update: Optional[str] = None # Could be appended
) -> AnalysisRun:
    """
    Update the status of an analysis run. Also updates timestamps.
    """
    db_run.status = status
    if status == AnalysisStatus.RUNNING and not db_run.started_at:
        db_run.started_at = datetime.utcnow()
    elif status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED] and not db_run.completed_at:
        db_run.completed_at = datetime.utcnow()

    if error_message:
        db_run.error_message = error_message
    if run_log_update:
        # Simple overwrite for now, could be append logic
        db_run.run_log = (db_run.run_log or "") + run_log_update

    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

def update_analysis_run_outputs( # A specific update function for outputs
    db: Session,
    *,
    db_run: AnalysisRun,
    output_artifacts: Dict[str, Any]
) -> AnalysisRun:
    """
    Update the output artifacts of a completed analysis run.
    """
    db_run.output_artifacts = output_artifacts
    # Optionally update status if not already completed
    if db_run.status != AnalysisStatus.COMPLETED and db_run.status != AnalysisStatus.FAILED:
         db_run.status = AnalysisStatus.COMPLETED # Assuming successful if outputs are set
         if not db_run.completed_at:
             db_run.completed_at = datetime.utcnow()

    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run


def update_analysis_run_internal( # More generic internal update
    db: Session,
    *,
    db_run: AnalysisRun,
    run_in: Union[AnalysisRunUpdateInternal, Dict[str, Any]]
) -> AnalysisRun:
    """
    Generic update for an analysis run by internal processes (e.g., Celery worker).
    """
    if isinstance(run_in, dict):
        update_data = run_in
    else:
        update_data = run_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_run, field, value)

    # Handle timestamp updates based on status changes if status is in update_data
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == AnalysisStatus.RUNNING and not db_run.started_at:
            db_run.started_at = datetime.utcnow()
        elif new_status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED] and not db_run.completed_at:
            db_run.completed_at = datetime.utcnow()


    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run


def remove_analysis_run(db: Session, *, analysis_run_id: uuid.UUID) -> Optional[AnalysisRun]:
    """
    Delete an analysis run record by its ID.
    Note: This does NOT delete any associated output files from S3/MinIO.
          That would be a separate operation.
    """
    run_to_delete = db.query(AnalysisRun).filter(AnalysisRun.id == analysis_run_id).first()
    if run_to_delete:
        db.delete(run_to_delete)
        db.commit()
    return run_to_delete