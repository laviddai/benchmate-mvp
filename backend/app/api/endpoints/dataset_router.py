# backend/app/api/endpoints/dataset_router.py
import uuid
from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import crud, models, schemas # Uses __init__.py for cleaner imports
from app.db.session import get_db
from app.services import s3_service # Import our S3 service
from app.core.config import settings # To get bucket names

# Import the placeholder for current user from project_router (or a shared auth module later)
from .project_router import get_current_active_user_placeholder


router = APIRouter()


@router.post("/upload-and-create/", response_model=schemas.DatasetRead, status_code=status.HTTP_201_CREATED)
async def upload_and_create_dataset_entry(
    *,
    db: Session = Depends(get_db),
    name: str = Form(...),
    project_id: uuid.UUID = Form(...),
    description: Optional[str] = Form(None),
    file_type: Optional[str] = Form(None), # e.g., csv, tsv, ome-tiff
    technique_type: Optional[str] = Form(None), # e.g., bulk_rna_seq
    metadata_json: Optional[str] = Form(None), # Optional: JSON string for metadata
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user_placeholder),
) -> Any:
    """
    Upload a dataset file to S3/MinIO and create its metadata entry in the database.
    Accepts form data including the file.
    """
    # 1. Ensure the project exists and the user has access (basic check for now)
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # Add authorization check: if current_user is not owner/member of project, raise 403

    # 2. Upload file to S3/MinIO
    # We can create a more structured object name, e.g., projects/{project_id}/datasets/{file.filename or uuid}
    # For simplicity now, just use the filename, but ensure it's unique or handle collisions.
    # A common pattern is to use a UUID for the object name to guarantee uniqueness.
    s3_object_name = f"projects/{project_id}/datasets/{uuid.uuid4()}_{file.filename}"

    try:
        s3_file_path = await s3_service.upload_file(
            file=file,
            bucket_name=settings.S3_BUCKET_NAME_DATASETS,
            object_name=s3_object_name
        )
        if not s3_file_path: # Should have raised HTTPException in s3_service if failed
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="File upload failed: No path returned.")
    except HTTPException as e:
        raise e # Re-raise HTTPExceptions from s3_service
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File upload to S3 failed: {str(e)}")

    # 3. Prepare dataset metadata for creation
    parsed_metadata: Optional[dict] = None
    if metadata_json:
        try:
            import json
            parsed_metadata = json.loads(metadata_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format for metadata_json.")

    dataset_in_data = {
        "name": name,
        "project_id": project_id,
        "description": description,
        "file_name": file.filename,
        "file_path_s3": s3_file_path, # Store the S3 key/path
        "file_type": file_type or file.content_type, # Use provided or from UploadFile
        "file_size_bytes": file.size if hasattr(file, 'size') and file.size is not None else None,
        "technique_type": technique_type,
        "metadata_": parsed_metadata
    }
    dataset_in = schemas.DatasetCreate(**dataset_in_data)

    # 4. Create dataset metadata entry in DB
    try:
        db_dataset = crud.create_dataset(db=db, dataset_in=dataset_in, uploaded_by_user_id=current_user.id)
    except ValueError as ve: # Catch ValueErrors from CRUD (e.g., project/user not found)
         # Potentially roll back S3 upload here or mark for cleanup if critical
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Potentially roll back S3 upload here or mark for cleanup if critical
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create dataset metadata in DB.")

    # For the response, generate a presigned URL for download if needed
    # This is just an example; you might not always want to return it immediately.
    presigned_url = s3_service.generate_presigned_url(
        bucket_name=settings.S3_BUCKET_NAME_DATASETS,
        object_name=s3_object_name # Use the same object name used for upload
    )
    # Manually construct the response as DatasetRead can't auto-create download_url from ORM
    dataset_response = schemas.DatasetRead.model_validate(db_dataset)
    dataset_response.download_url = presigned_url
    return dataset_response


@router.get("/project/{project_id}/", response_model=List[schemas.DatasetReadMinimal])
def read_datasets_by_project_id(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user_placeholder), # Auth placeholder
) -> Any:
    """
    Retrieve datasets for a specific project.
    (Authorization: user must be owner or member of project - to be implemented)
    """
    project = crud.get_project(db, project_id=project_id) # Fetch project to check access
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # Add authorization check here for current_user access to project

    datasets = crud.get_datasets_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return datasets


@router.get("/{dataset_id}", response_model=schemas.DatasetRead)
def read_dataset_by_id(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user_placeholder), # Auth placeholder
) -> Any:
    """
    Get a specific dataset by ID.
    (Authorization: user must have access to the dataset's project - to be implemented)
    """
    dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    # Add authorization check here for current_user access to dataset.project

    presigned_url = s3_service.generate_presigned_url(
        bucket_name=settings.S3_BUCKET_NAME_DATASETS, # Assuming datasets are in this bucket
        object_name=dataset.file_path_s3.split(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/")[-1] if dataset.file_path_s3.startswith(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/") else dataset.file_path_s3
    )
    dataset_response = schemas.DatasetRead.model_validate(dataset)
    dataset_response.download_url = presigned_url
    return dataset_response

# We can add PUT (update dataset metadata) and DELETE dataset (metadata + S3 file) later.