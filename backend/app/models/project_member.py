# backend/app/models/project_member.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, func, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User
    from .project import Project

class ProjectMember(Base):
    __tablename__ = "project_members"

    # Foreign keys to define the many-to-many relationship
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Additional attributes for the membership
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False) # e.g., "owner", "editor", "viewer"
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Composite primary key ---
    # Ensures that a user can only have one role per project.
    __table_args__ = (
        PrimaryKeyConstraint("project_id", "user_id", name="pk_project_members"),
        {}, # Other table args like unique constraints can go here if needed
    )

    # --- Relationships ---
    # Allows easy navigation from a ProjectMember instance back to Project and User
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members",
        lazy="selectin"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="project_memberships",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role='{self.role}')>"