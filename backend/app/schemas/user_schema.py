# backend/app/schemas/user_schema.py
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field

# --- User Base Schema ---
# Contains common fields shared across different User schemas.
class UserBase(BaseModel):
    email: Optional[EmailStr] = None # Using Pydantic's EmailStr for validation
    full_name: Optional[str] = None
    orcid_id: Optional[str] = None
    role: Optional[str] = "member" # Default role
    profile_data: Optional[dict] = None # For avatar URL, bio, etc.

    # Pydantic model configuration
    class Config:
        # This allows the Pydantic model to be created from ORM objects (SQLAlchemy models)
        # e.g., UserRead.model_validate(db_user_object)
        from_attributes = True


# --- User Create Schema ---
# Used when creating a new user.
# For ORCID login, we might not need a password.
# If you add email/password registration later, you'd include a password field here.
class UserCreate(UserBase):
    email: EmailStr # Email is required for creation
    orcid_id: Optional[str] = None # Will be set after successful ORCID auth
    # password: Optional[str] = None # If you add direct password registration

# --- User Update Schema ---
# Used when updating an existing user. All fields are optional.
class UserUpdate(UserBase):
    # password: Optional[str] = None # If allowing password updates
    pass # Inherits all optional fields from UserBase


# --- User Read Schema (Publicly readable User info) ---
# Properties to return to client when reading a user.
# Excludes sensitive information like hashed_password.
class UserRead(UserBase):
    id: uuid.UUID
    email: EmailStr # Make sure email is always present when reading
    role: str # Role should also be present
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    # We can add related project information if needed when fetching a user
    # projects_owned_count: Optional[int] = 0
    # project_memberships_count: Optional[int] = 0

# --- User In DB Schema ---
# Represents a user as stored in the database, including potentially sensitive fields.
# This is useful for internal representation or when converting from a DB object.
# Typically not directly exposed via API.
class UserInDB(UserBase):
    id: uuid.UUID
    hashed_password: Optional[str] = None # If you store hashed passwords
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None