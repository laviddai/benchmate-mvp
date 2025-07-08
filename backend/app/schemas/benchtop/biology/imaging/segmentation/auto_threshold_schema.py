# backend/app/schemas/benchtop/biology/imaging/segmentation/auto_threshold_schema.py

from pydantic import BaseModel, Field, field_validator

# This list should be kept in sync with the corresponding YAML config file
# to ensure the backend validates against the same options presented in the UI.
VALID_METHODS = [
    "Otsu", "Huang", "MaxEntropy", "Triangle", "Yen", "IsoData",
    "Li", "Mean", "MinError", "Minimum", "Moments", "Percentile",
    "RenyiEntropy", "Shanbhag"
]

class AutoThresholdParams(BaseModel):
    """
    Pydantic schema for Auto Threshold parameters.
    This defines the data contract for the tool's processor.
    """
    method: str = Field(..., description="The automatic thresholding algorithm to use.")

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate that the provided method is one of the supported algorithms."""
        if v not in VALID_METHODS:
            raise ValueError(f"Invalid threshold method '{v}'. Must be one of {VALID_METHODS}")
        return v

    class Config:
        from_attributes = True