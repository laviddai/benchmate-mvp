# backend/app/crud/crud_dataset.py
import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session, selectinload

from app.models.dataset import Dataset
from app.models.project import Project # Needed for type check or query
from app.models.user import User # Needed for type check or query
from app.schemas.dataset_schema import DatasetCreate, DatasetUpdate

def get_dataset(db: Session, dataset_id: uuid.UUID) -> Optional[Dataset]:
    """
    Retrieve a single dataset by its ID.
    Optionally eager load relationships like project and uploader.
    """
    return (
        db.query(Dataset)
        .options(selectinload(Dataset.project), selectinload(Dataset.uploader))
        .filter(Dataset.id == dataset_id)
        .first()
    )

def get_datasets_by_project(
    db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Dataset]:
    """
    Retrieve datasets belonging to a specific project with pagination.
    """
    return (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id)
        .options(selectinload(Dataset.uploader)) # Eager load uploader
        .order_by(Dataset.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_dataset(
    db: Session, *, dataset_in: DatasetCreate, uploaded_by_user_id: uuid.UUID
) -> Dataset:
    """
    Create a new dataset metadata record.
    `dataset_in` is a Pydantic model (DatasetCreate).
    `uploaded_by_user_id` is the ID of the user who uploaded the dataset.
    """
    # Ensure project and user exist (optional, but good practice if not handled by FK constraints immediately)
    project = db.query(Project).filter(Project.id == dataset_in.project_id).first()
    if not project:
        # In a real app, you'd raise an HTTPException here that the API endpoint can catch
        raise ValueError(f"Project with id {dataset_in.project_id} not found.")

    uploader = db.query(User).filter(User.id == uploaded_by_user_id).first()
    if not uploader:
        raise ValueError(f"User with id {uploaded_by_user_id} not found.")


    db_dataset_data = dataset_in.model_dump(exclude_unset=True)
    db_dataset = Dataset(**db_dataset_data, uploaded_by_user_id=uploaded_by_user_id)

    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

def update_dataset(
    db: Session,
    *,
    db_dataset: Dataset, # Existing SQLAlchemy Dataset model instance
    dataset_in: Union[DatasetUpdate, Dict[str, Any]] # Pydantic schema or dict
) -> Dataset:
    """
    Update an existing dataset's metadata.
    File path related fields (file_name, file_path_s3, file_size_bytes) are typically not updated here.
    """
    if isinstance(dataset_in, dict):
        update_data = dataset_in
    else:
        update_data = dataset_in.model_dump(exclude_unset=True)

    # Prevent updating fields that should be immutable after creation
    # (like file_path_s3, project_id, uploaded_by_user_id)
    # This logic can be more sophisticated in a service layer.
    immutable_fields = ["file_name", "file_path_s3", "file_size_bytes", "project_id", "uploaded_by_user_id", "id", "created_at"]
    for field in immutable_fields:
        if field in update_data:
            del update_data[field]

    for field, value in update_data.items():
        setattr(db_dataset, field, value)

    db.add(db_dataset) # SQLAlchemy tracks changes on the existing object
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

def remove_dataset(db: Session, *, dataset_id: uuid.UUID) -> Optional[Dataset]:
    """
    Delete a dataset metadata record by its ID.
    Note: This does NOT delete the actual file from S3/MinIO.
          That would be a separate operation, typically handled by the S3 service
          and coordinated by an API endpoint or a service layer function.
    """
    dataset_to_delete = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if dataset_to_delete:
        db.delete(dataset_to_delete)
        db.commit()
    return dataset_to_delete