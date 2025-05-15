from pydantic import Field
from .tool_base import ToolParams

class VolcanoParams(ToolParams):
    """
    Parameters specific to the volcano plot tool.
    """
    fold_change_threshold: float = Field(
        1.0, description="Log2 fold-change threshold for highlighting genes"
    )
    p_value_threshold: float = Field(
        0.05, description="Adjusted p-value threshold for highlighting genes"
    )
    label_top_n: int = Field(
        10, description="Number of top significant genes to label on plot"
    )