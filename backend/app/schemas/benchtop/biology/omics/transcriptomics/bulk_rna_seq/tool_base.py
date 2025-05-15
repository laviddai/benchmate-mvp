from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ToolParams(BaseModel):
    """
    Core inputs shared by all bulk RNA‑seq tools.
    """
    gene_col: Optional[str] = Field(None, description="Name of the gene identifier column")
    log2fc_col: Optional[str] = Field(None, description="Name of the log2 fold-change column")
    pvalue_col: Optional[str] = Field(None, description="Name of the p-value column")
    # Global options:
    export_format: Optional[str] = Field(None, description="Export format: PNG, SVG, PDF")
    color_scheme: Optional[str] = Field(None, description="Color scheme for plots")

class ToolResponse(BaseModel):
    """
    Common response: a data‑URI PNG plus summary stats.
    """
    plot_image: str = Field(..., description="Base64-encoded PNG data URI")
    summary: Dict[str, Any] = Field(..., description="Tool-specific summary statistics")