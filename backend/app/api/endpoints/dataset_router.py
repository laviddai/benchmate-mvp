# backend/app/api/endpoints/dataset_router.py
import uuid
import json
import logging # Import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db.session import get_db
from app.services import s3_service
from app.core.config import settings
from app.api.endpoints.project_router import get_current_active_user_placeholder

router = APIRouter()
logger = logging.getLogger(__name__) # Create a logger instance

@router.post("/upload-and-create/", response_model=schemas.DatasetRead)
async def upload_and_create_dataset_entry(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user_placeholder),
    # --- FIX: Explicitly add `name` as an expected Form field ---
    name: str = Form(...),
    project_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    file_type: Optional[str] = Form(None),
    technique_type: Optional[str] = Form(None),
    metadata_json: Optional[str] = Form(None),
):
    """
    Upload a dataset file to S3/MinIO and create its metadata entry in the database.
    Accepts form data including the file.
    """
    # --- FIX: Add a comprehensive try...except block for better error handling ---
    try:
        # 1. Ensure the project exists
        project = crud.get_project(db, project_id=project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        # Basic authorization placeholder can be added here later

        # 2. Get file size before consuming the stream
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # 3. Upload file to S3/MinIO
        s3_object_name = f"projects/{project_id}/datasets/{uuid.uuid4()}_{file.filename}"
        
        s3_file_path = await s3_service.upload_file(
            file=file,
            bucket_name=settings.S3_BUCKET_NAME_DATASETS,
            object_name=s3_object_name
        )
        if not s3_file_path:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file to S3")

        # 4. Prepare dataset metadata for creation
        parsed_metadata: Optional[dict] = None
        if metadata_json:
            try:
                parsed_metadata = json.loads(metadata_json)
            except json.JSONDecodeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON in metadata_json")

        dataset_in_data = {
            "project_id": project_id,
            "name": name, # Use the name from the form
            "description": description,
            "file_name": file.filename,
            "file_path_s3": s3_file_path,
            "file_size_bytes": file_size, # Use the size we determined earlier
            "file_type": file_type or file.content_type,
            "technique_type": technique_type,
            "metadata_": parsed_metadata
        }
        
        dataset_in = schemas.DatasetCreate(**{k: v for k, v in dataset_in_data.items() if v is not None})

        # 5. Create dataset metadata entry in DB
        db_dataset = crud.create_dataset(db=db, dataset_in=dataset_in, uploaded_by_user_id=current_user.id)
        
        # 6. Manually construct the response
        dataset_response = schemas.DatasetRead.model_validate(db_dataset)
        
        return dataset_response

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise http_exc
    except Exception as e:
        # Log the full, unexpected error for debugging
        logger.error(f"Error in upload_and_create_dataset_entry: {e}", exc_info=True)
        # Return a generic 500 error to the client
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An internal server error occurred: {e}")


# --- All other endpoints (GET, etc.) remain the same ---

@router.get("/project/{project_id}", response_model=List[schemas.DatasetRead])
def get_project_datasets(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user_placeholder),
):
    """
    Retrieve datasets for a specific project.
    """
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Add authorization check here later
    
    datasets = crud.get_datasets_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return datasets


@router.get("/{dataset_id}", response_model=schemas.DatasetRead)
def get_dataset_by_id(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user_placeholder),
):
    """
    Get a specific dataset by ID.
    """
    dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    
    # Add authorization check here later
    
    dataset_response = schemas.DatasetRead.model_validate(dataset)
    return dataset_response