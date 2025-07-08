# backend/app/schemas/benchtop/biology/imaging/filters/gaussian_blur_schema.py

from pydantic import BaseModel, Field

class GaussianBlurParams(BaseModel):
    """
    Pydantic schema for Gaussian Blur parameters.
    This defines the data contract for the tool's processor.
    """
    sigma: float = Field(..., description="Sigma value for the Gaussian kernel.", gt=0)

    class Config:
        # Pydantic v1 style config for compatibility if needed, can be model_config in v2
        from_attributes = True