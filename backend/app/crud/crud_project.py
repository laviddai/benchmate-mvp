# backend/app/crud/crud_project.py
import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, or_

from app.models.project import Project
from app.models.user import User
from app.models.project_member import ProjectMember
from app.schemas.project_schema import ProjectCreate, ProjectUpdate, ProjectMemberCreate, ProjectMemberUpdate


# --- Project CRUD ---

def get_project(db: Session, project_id: uuid.UUID) -> Optional[Project]:
    """
    Retrieve a single project by its ID.
    Optionally eager load owner and members.
    """
    return (
        db.query(Project)
        .options(selectinload(Project.owner), selectinload(Project.members).selectinload(ProjectMember.user))
        .filter(Project.id == project_id)
        .first()
    )

def get_projects_by_owner(
    db: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Project]:
    """
    Retrieve projects owned by a specific user with pagination.
    """
    return (
        db.query(Project)
        .filter(Project.created_by_user_id == owner_id)
        .options(selectinload(Project.owner)) # Eager load owner
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_projects_for_user(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Project]:
    """
    Retrieve projects a user is a member of (or owns) with pagination.
    """
    return (
        db.query(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .filter(
            or_(
                Project.created_by_user_id == user_id, # User owns the project
                ProjectMember.user_id == user_id       # User is a member of the project
            )
        )
        .options(selectinload(Project.owner), selectinload(Project.members).selectinload(ProjectMember.user))
        .order_by(Project.updated_at.desc())
        .distinct() # Ensure projects are not duplicated if user is owner AND member (though our model prevents this specific case)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_project(db: Session, *, project_in: ProjectCreate, owner_id: uuid.UUID) -> Project:
    """
    Create a new project.
    The owner_id is explicitly passed, typically from the authenticated user context.
    """
    db_project_data = project_in.model_dump(exclude_unset=True)
    db_project = Project(**db_project_data, created_by_user_id=owner_id)
    db.add(db_project)

    # Add the owner as a member with the 'owner' role
    owner_membership = ProjectMember(
        project_id=db_project.id, # This will be set after flush if not before
        user_id=owner_id,
        role="owner"
    )
    db.add(owner_membership)

    db.commit()
    db.refresh(db_project)
    # db.refresh(owner_membership) # Optional, if you need the refreshed membership object immediately
    return db_project


def update_project(
    db: Session,
    *,
    db_project: Project, # Existing SQLAlchemy Project model instance
    project_in: Union[ProjectUpdate, Dict[str, Any]] # Pydantic schema or dict for updates
) -> Project:
    """
    Update an existing project.
    """
    if isinstance(project_in, dict):
        update_data = project_in
    else:
        update_data = project_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_project, field, value)

    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def remove_project(db: Session, *, project_id: uuid.UUID) -> Optional[Project]:
    """
    Delete a project by its ID.
    Associated ProjectMember entries will be cascade deleted due to model definition.
    """
    project_to_delete = db.query(Project).filter(Project.id == project_id).first()
    if project_to_delete:
        db.delete(project_to_delete)
        db.commit()
    return project_to_delete


# --- ProjectMember CRUD ---

def get_project_member(
    db: Session, project_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[ProjectMember]:
    """
    Retrieve a specific project member entry.
    """
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .options(selectinload(ProjectMember.user)) # Eager load user details
        .first()
    )

def get_project_members(db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ProjectMember]:
    """
    Retrieve all members of a specific project with pagination.
    """
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id)
        .options(selectinload(ProjectMember.user)) # Eager load user details for each member
        .order_by(ProjectMember.joined_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def add_project_member(
    db: Session, *, project_id: uuid.UUID, member_in: ProjectMemberCreate
) -> Optional[ProjectMember]:
    """
    Add a user to a project with a specific role.
    Checks if the user already exists in the project.
    """
    existing_member = get_project_member(db, project_id=project_id, user_id=member_in.user_id)
    if existing_member:
        # Optionally, update the role if already a member, or raise an error/return existing
        # For now, let's just return the existing member to prevent duplicates from this function
        return existing_member # Or raise HTTPException(status_code=409, detail="User is already a member of this project")

    # Ensure the user exists (optional, but good practice)
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        return None # Or raise HTTPException(status_code=404, detail="User to add not found")

    db_member_data = member_in.model_dump() # No exclude_unset, role is required
    db_member = ProjectMember(project_id=project_id, **db_member_data)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def update_project_member_role(
    db: Session,
    *,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    member_in: ProjectMemberUpdate
) -> Optional[ProjectMember]:
    """
    Update the role of an existing project member.
    """
    db_member = get_project_member(db, project_id=project_id, user_id=user_id)
    if not db_member:
        return None # Or raise HTTPException(status_code=404, detail="Project member not found")

    update_data = member_in.model_dump(exclude_unset=True) # Only update provided fields (i.e., role)
    for field, value in update_data.items():
        setattr(db_member, field, value)

    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def remove_project_member(
    db: Session, *, project_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[ProjectMember]:
    """
    Remove a user from a project.
    """
    member_to_delete = get_project_member(db, project_id=project_id, user_id=user_id)
    if member_to_delete:
        # Prevent owner from being removed this way if it's the last owner or specific logic
        # For now, simple removal. More complex logic can be added in a service layer.
        # if member_to_delete.role == "owner" and member_to_delete.user_id == member_to_delete.project.created_by_user_id:
        #     # Potentially check if there are other owners before allowing removal
        #     pass
        db.delete(member_to_delete)
        db.commit()
    return member_to_delete