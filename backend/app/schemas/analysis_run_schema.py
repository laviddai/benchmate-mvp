# backend/app/schemas/analysis_run_schema.py
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field
from app.models.analysis_run import AnalysisStatus # Import the Enum

# Import other relevant schemas for nesting if needed
from .user_schema import UserRead
from .dataset_schema import DatasetReadMinimal

# --- AnalysisRun Base Schema ---
class AnalysisRunBase(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tool_id: Optional[str] = Field(None, max_length=255)
    tool_version: Optional[str] = Field(None, max_length=50)
    parameters: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# --- AnalysisRun Create Schema ---
# Data needed when initiating an analysis run (job submission)
class AnalysisRunCreate(AnalysisRunBase):
    tool_id: str = Field(..., max_length=255) # Tool ID is mandatory for creation
    project_id: uuid.UUID
    primary_input_dataset_id: Optional[uuid.UUID] = None # Or a list if supporting multiple
    # parameters will be passed, specific to the tool

    # Name can be auto-generated or user-provided
    name: Optional[str] = Field(None, max_length=255)


# --- AnalysisRun Update Schema ---
# Used by Celery workers or other internal processes to update status, results, logs.
# Not typically for direct user updates via API, except maybe for name/description.
class AnalysisRunUpdateInternal(BaseModel): # A more specific update schema
    status: Optional[AnalysisStatus] = None
    output_artifacts: Optional[Dict[str, Any]] = None
    run_log: Optional[str] = None # Or append to existing log
    error_message: Optional[str] = None
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True # For creating from an ORM object if needed

# Schema for users to update mutable fields like name/description
class AnalysisRunUserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

    class Config:
        from_attributes = True


# --- AnalysisRun Read Schema ---
# Data returned when reading an analysis run
class AnalysisRunRead(AnalysisRunBase):
    id: uuid.UUID
    status: AnalysisStatus
    project_id: uuid.UUID
    created_by_user_id: uuid.UUID # User who initiated the run

    primary_input_dataset_id: Optional[uuid.UUID] = None
    # primary_input_dataset: Optional[DatasetReadMinimal] = None # Nested info

    output_artifacts: Optional[Dict[str, Any]] = None
    run_log: Optional[str] = None # Might return a snippet or URL to full log
    error_message: Optional[str] = None

    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime # Record creation time
    updated_at: datetime # Record update time

    # creator: Optional[UserRead] = None # Nested creator info
    # project_name: Optional[str] = None # Could be denormalized or joined