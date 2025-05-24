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
    
    # Pydantic field name matches SQLAlchemy attribute name
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata") 
    # The 'alias' here means:
    # - For input JSON, it can accept "metadata" and map it to `metadata_`.
    # - For output JSON, it will serialize `metadata_` as "metadata".
    # When using from_attributes=True, it will look for an attribute named `metadata_` on the ORM object.
    
    technique_type: Optional[str] = Field(None, max_length=100)

    class Config:
        from_attributes = True
        populate_by_name = True # This makes Pydantic use aliases when populating from dicts/JSON
                                # and also when serializing to dicts/JSON.
                                # For from_attributes, it should still primarily look for the attribute name itself.


# --- Dataset Create Schema ---
class DatasetCreate(DatasetBase):
    name: str = Field(..., min_length=1, max_length=255)
    file_name: str
    file_path_s3: str
    file_size_bytes: Optional[int] = None
    project_id: uuid.UUID
    # metadata_ is inherited. When creating from JSON, if "metadata" key is present, it maps to metadata_.


# --- Dataset Update Schema ---
class DatasetUpdate(DatasetBase):
    pass


# --- Dataset Read Schema ---
class DatasetRead(DatasetBase):
    id: uuid.UUID
    name: str
    file_name: str
    file_path_s3: str
    file_size_bytes: Optional[int] = None
    # metadata_ is inherited. When serializing to JSON, it becomes "metadata".
    # When creating from ORM (db_dataset), it reads db_dataset.metadata_
    project_id: uuid.UUID
    uploaded_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
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