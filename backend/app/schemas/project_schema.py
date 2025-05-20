# backend/app/schemas/project_schema.py
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

# Import UserRead schema for nesting in ProjectRead if needed
from .user_schema import UserRead

# --- Project Base Schema ---
# Common fields for Project schemas
class ProjectBase(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    visibility: Optional[str] = Field("private", examples=["private", "shared_with_link", "public"])
    tags: Optional[List[str]] = Field(None, examples=[["RNA-seq", "cancer-research"]])

    class Config:
        from_attributes = True


# --- Project Create Schema ---
# Fields required when creating a new project.
class ProjectCreate(ProjectBase):
    name: str = Field(..., min_length=3, max_length=255) # Name is required for creation
    # created_by_user_id will be set by the backend based on the authenticated user


# --- Project Update Schema ---
# Fields allowed when updating an existing project. All are optional.
class ProjectUpdate(ProjectBase):
    pass # Inherits all optional fields from ProjectBase


# --- Project Read Schema ---
# Properties to return to client when reading a project.
class ProjectRead(ProjectBase):
    id: uuid.UUID
    created_by_user_id: uuid.UUID
    name: str # Ensure name is present
    visibility: str # Ensure visibility is present
    created_at: datetime
    updated_at: datetime

    # Optionally, include owner information when reading a project
    owner: Optional[UserRead] = None # Nested UserRead schema

    # You might add counts or summaries here later
    # dataset_count: Optional[int] = 0
    # member_count: Optional[int] = 0

# --- ProjectMember Base Schema ---
class ProjectMemberBase(BaseModel):
    role: Optional[str] = Field("member", examples=["owner", "editor", "viewer"])

    class Config:
        from_attributes = True

# --- ProjectMember Create Schema ---
# Used when adding a user to a project.
class ProjectMemberCreate(ProjectMemberBase):
    user_id: uuid.UUID # The ID of the user to add
    role: str = Field("member", examples=["owner", "editor", "viewer"]) # Role is required

# --- ProjectMember Update Schema ---
# Used when changing a member's role in a project.
class ProjectMemberUpdate(ProjectMemberBase):
    role: str # Role is required for update

# --- ProjectMember Read Schema ---
# Properties to return when reading project membership details.
class ProjectMemberRead(ProjectMemberBase):
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    user: Optional[UserRead] = None # Include details of the member user
    # project: Optional[ProjectRead] = None # Could include project details but might be redundant if fetching members of a specific project

# Minimal schema for a project with its members
class ProjectWithMembersRead(ProjectRead):
    members: List[ProjectMemberRead] = []