# backend/app/models/project.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional # For type hinting relationships

from sqlalchemy import String, DateTime, func, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User  # For relationship type hinting
    from .project_member import ProjectMember # For relationship type hinting
    from .dataset import Dataset # For Dataset relationship
    # from .analysis_run import AnalysisRun # For future AnalysisRun relationship

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    visibility: Mapped[str] = mapped_column(String(50), default="private", nullable=False) # e.g., "private", "shared_with_link", "public"
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True) # Store as a list of strings

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Relationships ---
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects_owned",
        foreign_keys=[created_by_user_id], # Specify if there are multiple FKs to User table
        lazy="selectin"
    )

    members: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan" # If a project is deleted, all its memberships are also deleted
    )

    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan" # If a project is deleted, its datasets are also deleted
    )
    # Future relationships:
    # analysis_runs: Mapped[List["AnalysisRun"]] = relationship("AnalysisRun", back_populates="project", lazy="selectin", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"