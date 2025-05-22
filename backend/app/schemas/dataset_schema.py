# backend/app/schemas/dataset_schema.py
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field

# --- Dataset Base Schema ---
class DatasetBase(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    file_type: Optional[str] = Field(None, max_length=50)
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata") # Alias for input/output
    technique_type: Optional[str] = Field(None, max_length=100)

    class Config:
        from_attributes = True
        # Allows using 'metadata' in Python code and 'metadata_' in Pydantic model
        # if you need to differentiate, or just use metadata_ consistently.
        # For simplicity, we can just use metadata_ in the model and expect metadata_ in API.
        # If you want API to use 'metadata' but model has 'metadata_', use populate_by_name
        # populate_by_name = True


# --- Dataset Create Schema ---
# Information needed when creating a dataset record (typically after file upload)
class DatasetCreate(DatasetBase):
    name: str = Field(..., min_length=1, max_length=255)
    file_name: str # Original filename from upload
    file_path_s3: str # S3 key provided by the upload service
    file_size_bytes: Optional[int] = None
    project_id: uuid.UUID
    # uploaded_by_user_id will be set by the backend

# --- Dataset Update Schema ---
class DatasetUpdate(DatasetBase):
    # Only name, description, metadata, technique_type can be updated
    # File path and original file info should generally not change after creation
    pass


# --- Dataset Read Schema ---
# Information returned when reading a dataset
class DatasetRead(DatasetBase):
    id: uuid.UUID
    name: str
    file_name: str
    file_path_s3: str # Usually you'd return a presigned URL instead of the direct S3 path
    file_size_bytes: Optional[int] = None
    project_id: uuid.UUID
    uploaded_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # For API response, you might want a temporary, downloadable URL
    download_url: Optional[str] = None


# Schema for dataset listing, potentially with less detail
class DatasetReadMinimal(BaseModel):
    id: uuid.UUID
    name: str
    file_type: Optional[str] = None
    technique_type: Optional[str] = None
    updated_at: datetime
    project_id: uuid.UUID

    class Config:
        from_attributes = True