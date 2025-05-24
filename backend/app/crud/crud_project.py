# backend/app/crud/crud_project.py
import uuid
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, or_

from app.models.project import Project
from app.models.user import User # Make sure User is imported
from app.models.project_member import ProjectMember
from app.schemas.project_schema import ProjectCreate, ProjectUpdate, ProjectMemberCreate, ProjectMemberUpdate


# --- Project CRUD ---
# ... (get_project, get_projects_by_owner, get_projects_for_user remain the same) ...
def get_project(db: Session, project_id: uuid.UUID) -> Optional[Project]:
    return (
        db.query(Project)
        .options(selectinload(Project.owner), selectinload(Project.members).selectinload(ProjectMember.user))
        .filter(Project.id == project_id)
        .first()
    )

def get_projects_by_owner(
    db: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Project]:
    return (
        db.query(Project)
        .filter(Project.created_by_user_id == owner_id)
        .options(selectinload(Project.owner))
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_projects_for_user(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Project]:
    return (
        db.query(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .filter(
            or_(
                Project.created_by_user_id == user_id,
                ProjectMember.user_id == user_id
            )
        )
        .options(selectinload(Project.owner), selectinload(Project.members).selectinload(ProjectMember.user))
        .order_by(Project.updated_at.desc())
        .distinct()
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_project(db: Session, *, project_in: ProjectCreate, owner_id: uuid.UUID) -> Project:
    """
    Create a new project.
    The owner_id is explicitly passed, typically from the authenticated user context.
    """
    owner_user = db.query(User).filter(User.id == owner_id).first()
    if not owner_user:
        raise ValueError(f"Owner user with id {owner_id} not found.") # Or HTTPException in API layer

    db_project_data = project_in.model_dump(exclude_unset=True)
    db_project = Project(**db_project_data, owner=owner_user) # Assign owner object directly

    # Create the ProjectMember instance for the owner
    # And associate it with the project and user using the relationship attributes
    owner_membership = ProjectMember(role="owner")
    owner_membership.user = owner_user   # Link to the User object
    owner_membership.project = db_project # Link to the Project object

    # Add to session. SQLAlchemy will figure out the order.
    # When db_project is added, its ID is generated (if not already set by Python default).
    # When owner_membership is processed, its project_id will be populated from db_project.
    db.add(db_project)
    db.add(owner_membership) # Or db_project.members.append(owner_membership) if cascade is set for save-update

    db.commit()
    db.refresh(db_project) # Refresh to get all attributes, including any loaded relationships
    # To access db_project.members immediately after commit and see the owner_membership,
    # you might need to refresh that relationship or the owner_membership object itself.
    # For now, returning db_project is the primary goal.
    return db_project

# ... (update_project, remove_project, and ProjectMember CRUD functions remain the same) ...
def update_project(
    db: Session,
    *,
    db_project: Project, 
    project_in: Union[ProjectUpdate, Dict[str, Any]]
) -> Project:
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
    project_to_delete = db.query(Project).filter(Project.id == project_id).first()
    if project_to_delete:
        db.delete(project_to_delete)
        db.commit()
    return project_to_delete

def get_project_member(
    db: Session, project_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[ProjectMember]:
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .options(selectinload(ProjectMember.user)) 
        .first()
    )

def get_project_members(db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ProjectMember]:
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id)
        .options(selectinload(ProjectMember.user)) 
        .order_by(ProjectMember.joined_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def add_project_member(
    db: Session, *, project_id: uuid.UUID, member_in: ProjectMemberCreate
) -> Optional[ProjectMember]:
    existing_member = get_project_member(db, project_id=project_id, user_id=member_in.user_id)
    if existing_member:
        return existing_member

    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        return None 

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None # Should not happen if project_id is validated at API layer

    db_member_data = member_in.model_dump() 
    db_member = ProjectMember(**db_member_data)
    db_member.project = project # Link to project
    db_member.user = user       # Link to user

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
    db_member = get_project_member(db, project_id=project_id, user_id=user_id)
    if not db_member:
        return None

    update_data = member_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_member, field, value)

    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def remove_project_member(
    db: Session, *, project_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[ProjectMember]:
    member_to_delete = get_project_member(db, project_id=project_id, user_id=user_id)
    if member_to_delete:
        db.delete(member_to_delete)
        db.commit()
    return member_to_delete