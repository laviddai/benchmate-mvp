# backend/app/crud/crud_user.py
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session
from sqlalchemy import func # For functions like count

from app.models.user import User # Your SQLAlchemy model
from app.schemas.user_schema import UserCreate, UserUpdate # Your Pydantic schemas

# Note: Password hashing is not implemented here yet.
# If you add direct password registration, you'd integrate password hashing.

def get_user(db: Session, user_id: Any) -> Optional[User]:
    """
    Retrieve a single user by their ID.
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a single user by their email address.
    """
    return db.query(User).filter(func.lower(User.email) == func.lower(email)).first()

def get_user_by_orcid_id(db: Session, orcid_id: str) -> Optional[User]:
    """
    Retrieve a single user by their ORCID ID.
    """
    return db.query(User).filter(User.orcid_id == orcid_id).first()

def get_users(
    db: Session, skip: int = 0, limit: int = 100
) -> List[User]:
    """
    Retrieve a list of users with pagination.
    """
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, *, user_in: UserCreate) -> User:
    """
    Create a new user.
    `user_in` is a Pydantic model (UserCreate).
    """
    # Create a dictionary from the Pydantic model, excluding unset fields
    # so that SQLAlchemy model defaults are used if a field isn't provided.
    db_user_data = user_in.model_dump(exclude_unset=True)

    # If you were implementing password hashing for direct registration:
    # if user_in.password:
    #     hashed_password = get_password_hash(user_in.password) # You'd need this helper
    #     db_user_data["hashed_password"] = hashed_password
    #     del db_user_data["password"] # Don't store plain password

    db_user = User(**db_user_data) # Create SQLAlchemy User model instance
    db.add(db_user)
    db.commit() # Commit the session to save the user to the database
    db.refresh(db_user) # Refresh the instance to get any DB-generated values (like ID, created_at)
    return db_user

def update_user(
    db: Session,
    *,
    db_user: User, # The existing SQLAlchemy User model instance
    user_in: Union[UserUpdate, Dict[str, Any]] # Pydantic schema or dict for updates
) -> User:
    """
    Update an existing user.
    `db_user` is the SQLAlchemy model instance fetched from the DB.
    `user_in` can be a Pydantic UserUpdate model or a dictionary of fields to update.
    """
    if isinstance(user_in, dict):
        update_data = user_in
    else:
        # Get data from Pydantic model, excluding unset fields
        # so we only update fields that were actually provided.
        update_data = user_in.model_dump(exclude_unset=True)

    # If you were implementing password updates:
    # if "password" in update_data and update_data["password"]:
    #     hashed_password = get_password_hash(update_data["password"])
    #     db_user.hashed_password = hashed_password
    #     del update_data["password"] # Don't store plain password

    for field, value in update_data.items():
        setattr(db_user, field, value) # Set attributes on the SQLAlchemy model

    db.add(db_user) # Add the updated object to the session (SQLAlchemy tracks changes)
    db.commit()
    db.refresh(db_user)
    return db_user

def remove_user(db: Session, *, user_id: Any) -> Optional[User]:
    """
    Delete a user by their ID.
    Returns the deleted user object or None if not found.
    """
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()
    return user_to_delete

# You might add other specific utility functions here, e.g.:
# def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
#     user = get_user_by_email(db, email=email)
#     if not user:
#         return None
#     if not verify_password(password, user.hashed_password): # You'd need these helpers
#         return None
#     return user

# def is_admin(user: User) -> bool:
#     return user.role == "admin"