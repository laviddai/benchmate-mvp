# backend/app/models/analysis_run.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any, List

from sqlalchemy import String, DateTime, func, ForeignKey, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum # For Python Enum

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User
    from .project import Project
    from .dataset import Dataset # For input/output datasets

# Define an Enum for Analysis Status
class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True) # User-defined name for this run
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tool_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True) # e.g., "volcano_plot_v1", "imaging_segmentation_cellpose"
    tool_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Version of the tool/script used

    # Parameters used for this specific run
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Status of the analysis
    status: Mapped[AnalysisStatus] = mapped_column(
        SAEnum(AnalysisStatus, name="analysis_status_enum", create_type=True), # Use native DB Enum if possible
        default=AnalysisStatus.PENDING,
        nullable=False,
        index=True
    )

    # Input Datasets (Many-to-Many relationship via an association table)
    # We'll define the association table 'analysis_input_datasets' later if needed for rich M2M.
    # For a simpler start, if an analysis run has one primary input dataset:
    primary_input_dataset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True, index=True
    )

    # Output Artifacts (e.g., path to plot image, path to results table in S3)
    # This could be a JSON field storing a list of output URIs or a link to another table.
    output_artifacts: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    # Example: {"plot_image_s3_path": "s3://...", "results_table_s3_path": "s3://...", "summary_stats": {...}}

    # Log output or error messages
    run_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Could also be an S3 path to a log file
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # If status is FAILED

    # Timestamps for the run
    queued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Foreign Keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Standard created_at/updated_at for the record itself
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


    # --- Relationships ---
    project: Mapped["Project"] = relationship(
        back_populates="analysis_runs", # We'll add 'analysis_runs' to Project model
        lazy="selectin"
    )
    creator: Mapped["User"] = relationship(
        # No back_populates needed if User doesn't directly list all analysis_runs created by them
        # If it does, add foreign_keys=[created_by_user_id]
        lazy="selectin"
    )
    primary_input_dataset: Mapped[Optional["Dataset"]] = relationship(
        # "Dataset",
        foreign_keys=[primary_input_dataset_id],
        # No back_populates if Dataset doesn't directly link back this way for primary input
        lazy="selectin"
    )

    # If using a many-to-many for input_datasets:
    # input_datasets: Mapped[List["Dataset"]] = relationship(
    #     secondary="analysis_input_datasets", # Name of the association table
    #     back_populates="input_for_analyses"
    # )

    def __repr__(self):
        return f"<AnalysisRun(id={self.id}, tool_id='{self.tool_id}', status='{self.status.value}')>"