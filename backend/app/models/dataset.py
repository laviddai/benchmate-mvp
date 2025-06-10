# backend/app/models/dataset.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import String, DateTime, func, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User
    from .project import Project
    # from .analysis_run import AnalysisRun # For future relationships

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # File-related information
    file_name: Mapped[str] = mapped_column(String(512), nullable=False) # Original uploaded filename
    file_path_s3: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True) # Key in S3/MinIO bucket
    file_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # e.g., "csv", "xlsx", "ome-tiff"
    file_size_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Metadata specific to the dataset type (e.g., column names for tabular data, dimensions for images)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True) # Renamed to avoid conflict with SQLAlchemy's .metadata

    # Technique type (linking to your YAML config concept)
    technique_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True) # e.g., "bulk_rna_seq", "imaging_segmentation"

    # Foreign Keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # --- Relationships ---
    project: Mapped["Project"] = relationship(
        # "Project", # String form not needed if Project is imported in TYPE_CHECKING
        back_populates="datasets", # We'll need to add 'datasets' relationship to Project model
        lazy="selectin"
    )
    uploader: Mapped["User"] = relationship(
        # "User",
        # No back_populates needed if User model doesn't directly list all datasets uploaded by them as a primary relationship.
        # If it does, add foreign_keys=[uploaded_by_user_id]
        lazy="selectin"
    )

    # Future: Link to AnalysisRuns where this dataset is an input or output
    # input_for_analyses: Mapped[List["AnalysisRun"]] = relationship(
    #     "AnalysisRun",
    #     secondary="analysis_input_datasets", # An association table
    #     back_populates="input_datasets"
    # )
    # output_of_analysis: Mapped[Optional["AnalysisRun"]] = relationship(
    #     "AnalysisRun",
    #     foreign_keys="[AnalysisRun.output_dataset_id]", # If an AnalysisRun directly produces one dataset
    #     back_populates="output_dataset"
    # )


    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}', project_id={self.project_id})>"