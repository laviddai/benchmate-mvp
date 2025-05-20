# backend/app/api/endpoints/user_router.py
import uuid
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas # Uses the __init__.py files for cleaner imports
from app.db.session import get_db # Dependency to get DB session

router = APIRouter()

# For now, these endpoints are open for development purposes.
# We will add authentication and authorization dependencies later.

@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_new_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    This will eventually be primarily driven by ORCID signup.
    For development, we allow direct creation.
    """
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    if user_in.orcid_id:
        user_by_orcid = crud.get_user_by_orcid_id(db, orcid_id=user_in.orcid_id)
        if user_by_orcid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this ORCID ID already exists.",
            )
    new_user = crud.create_user(db=db, user_in=user_in)
    return new_user


@router.get("/", response_model=List[schemas.UserRead])
def read_users_list(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    # current_user: models.User = Depends(get_current_active_admin_user) # Add auth later
) -> Any:
    """
    Retrieve users (paginated).
    Eventually, this should be restricted to admin users.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.UserRead)
def read_user_by_id(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    # current_user: models.User = Depends(get_current_active_user) # Add auth later
) -> Any:
    """
    Get a specific user by ID.
    Eventually, check if current_user is the user_id or an admin.
    """
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# We can add PUT (update) and DELETE user endpoints later as needed,
# ensuring proper authorization.