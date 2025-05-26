# app/schemas/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.py

from typing import Optional, Dict
from pydantic import BaseModel, Field

from .tool_base import ToolParams  # import your common base class


class VolcanoParams(ToolParams):
    """
    Parameters accepted by the bulk-RNA-seq volcano-plot processor.
    Inherits common options (project_id, etc.) from ToolParams.
    """

    # ────────── NEW FIELD ──────────
    analysis_name: Optional[str] = Field(
        default=None,
        description="Human-readable name for this analysis run; "
                    "used as the default matplotlib title if provided.",
    )

    # ────────── Data-column names ──────────
    gene_col: str = Field(
        default="Gene",
        description="Column that contains gene identifiers.",
    )
    log2fc_col: str = Field(
        default="logFC",
        description="Column that contains log2 fold-change values.",
    )
    pvalue_col: str = Field(
        default="PValue",
        description="Column that contains p-values (not −log10).",
    )

    # ────────── Thresholds / visual options ──────────
    fold_change_threshold: float = Field(
        default=1.0,
        description="Absolute log2FC threshold used to colour points.",
    )
    p_value_threshold: float = Field(
        default=0.05,
        description="P-value cut-off used to colour points.",
    )
    label_top_n: int = Field(
        default=10,
        ge=0,
        description="Number of most significant genes to label on the plot.",
    )
    color_scheme: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom hex colours for {'up', 'down', 'neutral'} points.",
    )
    export_format: Optional[str] = Field(
        default=None,
        description="If set (e.g. 'png', 'svg'), processor saves the plot "
                    "to this format in addition to returning the figure.",
    )

    # ────────── Pydantic config ──────────
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
