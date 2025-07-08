# backend/app/schemas/benchtop/biology/omics/transcriptomics/bulk_rna_seq/heatmap_schema.py

from typing import Optional, List
from pydantic import BaseModel, Field

class HeatmapParams(BaseModel):
    """
    Pydantic schema for Heatmap parameters.
    This defines the data contract for the tool's processor and API endpoint.
    """
    analysis_name: Optional[str] = Field("Gene Expression Heatmap", description="Name for the analysis run.")
    gene_selection_method: str = Field("top_n_variable", description="Method to select genes for plotting.")
    top_n_genes: int = Field(50, description="Number of genes for 'top_n_variable' method.")
    de_logfc_threshold: float = Field(1.0, description="LogFC threshold for 'de_genes' method.")
    de_pvalue_threshold: float = Field(0.05, description="P-value/FDR threshold for 'de_genes' method.")
    gene_list: Optional[List[str]] = Field(None, description="A specific list of genes to plot.")
    normalization_method: str = Field("log2_transform", description="How to normalize data before scaling.")
    scaling_method: str = Field("z_score_row", description="How to scale data for visualization.")
    cluster_genes: bool = Field(True, description="Whether to cluster genes (rows).")
    cluster_samples: bool = Field(True, description="Whether to cluster samples (columns).")
    clustering_method: str = Field("average", description="Hierarchical clustering linkage method.")
    distance_metric: str = Field("euclidean", description="Distance metric for clustering.")

    class Config:
        # Pydantic v1 style config for compatibility if needed, can be model_config in v2
        from_attributes = True