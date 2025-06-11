# backend/app/api/endpoints/file_router.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.services import s3_service # Import our S3 service
from app.core.config import settings # To validate bucket names if needed

# Import the placeholder for current user (replace with actual auth later)
# For now, this endpoint might be relatively open for authenticated users,
# but proper authorization (e.g., can this user access this specific file?)
# would be added based on project/dataset ownership or membership.
from .project_router import get_current_active_user_placeholder
from app import models # For current_user type hint

router = APIRouter()

class PresignedUrlResponse(BaseModel):
    url: str
    object_key: str
    bucket_name: str
    method: str = "GET" # Default method for which URL is generated


@router.get("/presigned-url/", response_model=PresignedUrlResponse)
async def get_s3_presigned_url(
    bucket_name: str = Query(..., description="The S3 bucket name."),
    object_key: str = Query(..., description="The S3 object key (path to the file within the bucket)."),
    expires_in: int = Query(3600, description="Expiration time for the URL in seconds.", ge=60, le=604800), # Min 1 min, Max 7 days
    # current_user: models.User = Depends(get_current_active_user_placeholder) # Auth placeholder
):
    """
    Generate a presigned URL for accessing an S3 object.

    **Authorization for accessing the specific object needs to be implemented.**
    For example, check if the current_user has rights to view the project/dataset
    associated with this S3 object_key.
    """

    # Basic validation: Ensure bucket_name is one of our known buckets
    # This is a simple security measure to prevent requests for arbitrary buckets.
    allowed_buckets = [
        settings.S3_BUCKET_NAME_DATASETS,
        settings.S3_BUCKET_NAME_RESULTS
    ]
    if bucket_name not in allowed_buckets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Access to bucket '{bucket_name}' is not permitted or bucket is invalid."
        )

    # TODO: Implement fine-grained authorization here:
    # 1. Determine which resource (Dataset, AnalysisRun output, etc.) this object_key belongs to.
    #    This might involve parsing the object_key or looking up a mapping in the database.
    #    For example, if object_key is "analysis_runs/{run_id}/results/plot.png", extract run_id.
    # 2. Fetch the associated Project from the database.
    # 3. Check if current_user is an owner or member of that Project.
    # 4. If not authorized, raise HTTPException(status_code=status.HTTP_403_FORBIDDEN).
    # For now, we proceed without this detailed check for development.
    print(f"Presigned URL requested for: bucket='{bucket_name}', key='{object_key}' by user (placeholder)")


    url = s3_service.generate_presigned_url(
        bucket_name=bucket_name,
        object_key=object_key,
        expiration=expires_in
    )

    if not url:
        # This could happen if the object doesn't exist or s3_service had an issue.
        # s3_service.generate_presigned_url logs errors.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 500 if it's an S3 service issue
            detail=f"Could not generate presigned URL. Object may not exist or S3 service error."
        )

    return PresignedUrlResponse(
        url=url,
        object_key=object_key,
        bucket_name=bucket_name
    )