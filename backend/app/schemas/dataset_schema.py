# backend/app/schemas/dataset_schema.py
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, ConfigDict # Import ConfigDict

# --- Dataset Base Schema ---
class DatasetBase(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    file_type: Optional[str] = Field(None, max_length=50)
    
    # This is the Python attribute name in the Pydantic model.
    # It should match the attribute on your SQLAlchemy model (Dataset.metadata_).
    metadata_: Optional[Dict[str, Any]] = Field(default=None)
    
    technique_type: Optional[str] = Field(None, max_length=100)

    # Use Pydantic v2 style model_config
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True # Allows aliases to be used for validation from dicts and serialization to dicts.
                              # For from_attributes, Pydantic will primarily look for the actual attribute name (`metadata_`).
    )


# --- Dataset Create Schema ---
class DatasetCreate(DatasetBase):
    name: str = Field(..., min_length=1, max_length=255)
    file_name: str
    file_path_s3: str
    file_size_bytes: Optional[int] = None
    project_id: uuid.UUID
    # metadata_ is inherited. `validation_alias="metadata"` will handle incoming JSON.


# --- Dataset Update Schema ---
class DatasetUpdate(DatasetBase):
    pass # metadata_ is inherited


# --- Dataset Read Schema ---
class DatasetRead(DatasetBase): # Inherits model_config from DatasetBase
    id: uuid.UUID
    name: str
    file_name: str
    file_path_s3: str
    file_size_bytes: Optional[int] = None
    # metadata_ is inherited. `from_attributes=True` in config will read `db_dataset.metadata_`.
    # `serialization_alias="metadata"` will ensure it's output as "metadata" in JSON.
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
    # If you want metadata here, add:
    # metadata_: Optional[Dict[str, Any]] = Field(
    #     default=None,
    #     validation_alias="metadata",
    #     serialization_alias="metadata"
    # )

    model_config = ConfigDict( # Ensure this also has the config if not inheriting from DatasetBase directly
        from_attributes=True,
        populate_by_name=True
    )