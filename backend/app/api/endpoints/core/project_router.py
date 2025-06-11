# backend/app/api/endpoints/project_router.py
import uuid
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas # Uses __init__.py for cleaner imports
from app.db.session import get_db

router = APIRouter()

# Placeholder for authenticated user - replace with actual auth dependency later
# For now, we'll need to manually pass owner_id or simulate it.
# A more robust way for dev might be a header with a fixed user_id.
def get_current_active_user_placeholder(db: Session = Depends(get_db)) -> models.User:
    # THIS IS A PLACEHOLDER - REPLACE WITH REAL AUTHENTICATION
    # For development, let's assume a default user exists or create one.
    # In a real app, this dependency would verify JWT and return the user.
    user = crud.get_user_by_email(db, email="dev_user@example.com")
    if not user:
        user_in = schemas.UserCreate(email="dev_user@example.com", full_name="Dev User")
        user = crud.create_user(db, user_in=user_in)
    return user


@router.post("/", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
def create_new_project(
    *,
    db: Session = Depends(get_db),
    project_in: schemas.ProjectCreate,
    current_user: models.User = Depends(get_current_active_user_placeholder), # Replace with real auth
) -> Any:
    """
    Create new project. The current authenticated user becomes the owner.
    """
    project = crud.create_project(db=db, project_in=project_in, owner_id=current_user.id)
    return project


@router.get("/", response_model=List[schemas.ProjectRead])
def read_projects_for_current_user(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user_placeholder), # Replace with real auth
) -> Any:
    """
    Retrieve projects for the current user (owned or member of).
    """
    # If you want only projects owned by the user:
    # projects = crud.get_projects_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    # For projects user is member of or owns:
    projects = crud.get_projects_for_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return projects


@router.get("/{project_id}", response_model=schemas.ProjectWithMembersRead) # Using ProjectWithMembersRead
def read_project_by_id(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user_placeholder), # Replace with real auth
) -> Any:
    """
    Get a specific project by ID.
    (Authorization: user must be owner or member - to be implemented)
    """
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Basic authorization placeholder:
    is_owner = project.created_by_user_id == current_user.id
    is_member = any(member.user_id == current_user.id for member in project.members) # project.members is eager loaded

    if not (is_owner or is_member) and not (current_user.role == "admin"): # Basic admin override
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return project

@router.post("/{project_id}/members/", response_model=schemas.ProjectMemberRead, status_code=status.HTTP_201_CREATED)
def add_member_to_project(
    project_id: uuid.UUID,
    *,
    db: Session = Depends(get_db),
    member_in: schemas.ProjectMemberCreate,
    current_user: models.User = Depends(get_current_active_user_placeholder), # Replace with real auth
) -> Any:
    """
    Add a user to a project.
    (Authorization: current_user must be project owner/admin - to be implemented)
    """
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # Add authorization check: e.g., if current_user.id != project.created_by_user_id: raise 403

    member = crud.add_project_member(db, project_id=project_id, member_in=member_in)
    if not member:
        # This could be because user to add doesn't exist, or already a member (depending on CRUD logic)
        # For now, crud.add_project_member handles if user to add not found by returning None.
        # It returns existing member if already present. Let's refine this if needed.
        user_to_add = crud.get_user(db, user_id=member_in.user_id)
        if not user_to_add:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {member_in.user_id} not found to add as member.")
        # If user exists but still no member, it means they were already a member (based on current crud_project)
        # Consider if this endpoint should update role if already member, or just add if not.
        # For now, assume add_project_member handles it.
        existing_member = crud.get_project_member(db, project_id=project_id, user_id=member_in.user_id)
        if existing_member and existing_member.role == member_in.role:
            return existing_member # Already exists with same role
        elif existing_member:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User is already a member with role '{existing_member.role}'. Use update endpoint to change role.")


    return member

# We can add PUT (update project), DELETE project, update member role, remove member endpoints later.