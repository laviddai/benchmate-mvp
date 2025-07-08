# backend/app/schemas/benchtop/biology/omics/transcriptomics/bulk_rna_seq/pca_schema.py

from typing import Optional
from pydantic import BaseModel, Field

class PCAParams(BaseModel):
    """
    Pydantic schema for PCA Plot parameters.
    This defines the data contract for the tool's processor and API endpoint.
    """
    analysis_name: Optional[str] = Field("Principal Component Analysis", description="Name for the analysis run.")
    grouping_column: Optional[str] = Field(None, description="Column name for grouping/coloring samples.")
    scale_data: bool = Field(True, description="Whether to scale data before PCA.")
    n_components: int = Field(10, description="Number of principal components to compute.")
    pc_x_axis: int = Field(1, description="Principal component for the X-axis.")
    pc_y_axis: int = Field(2, description="Principal component for the Y-axis.")

    class Config:
        # Pydantic v1 style config for compatibility if needed, can be model_config in v2
        from_attributes = True