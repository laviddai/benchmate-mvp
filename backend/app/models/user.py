# backend/app/models/user.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional # For type hinting relationships

from sqlalchemy import String, DateTime, JSON, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID # Specific UUID type for PostgreSQL

from app.db.base_class import Base # Import the Base we created

if TYPE_CHECKING:
    from .project import Project  # For relationship type hinting
    from .project_member import ProjectMember # For relationship type hinting


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    orcid_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # For potential future password auth
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False) # e.g., "member", "admin"

    # Foreign key for plan_id - assuming a 'plans' table might exist later
    # plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign key for institution_id - assuming an 'institutions' table might exist later
    # institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=True)

    profile_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # For avatar URL, bio, etc.

    # --- Relationships ---
    # 'lazy="selectin"' is a good default loading strategy for many-to-one or one-to-many.
    # It loads related objects via a separate SELECT statement when the attribute is accessed.

    # Projects directly owned by this user
    projects_owned: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="owner",
        foreign_keys="[Project.created_by_user_id]", # Explicitly specify foreign keys if ambiguous
        lazy="selectin"
    )

    # Membership entries linking this user to various projects
    project_memberships: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan" # If a user is deleted, their memberships are also deleted
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"