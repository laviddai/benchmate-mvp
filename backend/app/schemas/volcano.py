from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class VolcanoParams(BaseModel):
    """
    Defines the optional column‐mapping parameters that users can
    supply via form data to override default column names.
    """
    pvalue_col: Optional[str] = Field(
        None, title="P-value Column", description="Name of the column containing p-values"
    )
    log2fc_col: Optional[str] = Field(
        None, title="Log2-FC Column", description="Name of the column containing log2 fold changes"
    )
    gene_col: Optional[str] = Field(
        None, title="Gene Column", description="Name of the column containing gene identifiers"
    )

class VolcanoResponse(BaseModel):
    """
    The shape of the JSON returned by the /run endpoint.
    """
    plot_image: str = Field(
        ...,
        title="Base64 Plot Image",
        description="Data-URI (base64) of the generated volcano plot in PNG format"
    )
    summary: Optional[Dict[str, Any]] = Field(
        None,
        title="Summary Statistics",
        description="Optional summary statistics (e.g. number of up/down-regulated genes)"
    )
