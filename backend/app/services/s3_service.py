# backend/app/services/s3_service.py
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException, status
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        if not all([settings.S3_ENDPOINT_URL, settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY]):
            logger.warning("S3 service is not fully configured. Some operations might fail.")
            self.s3_client = None
            self.s3_resource = None
            return

        try:
            # When using MinIO or other S3-compatible services,
            # signature_version='s3v4' and region_name might be important.
            # address_style='path' is sometimes needed for MinIO if virtual host style isn't working.
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION_NAME, # Often needed by boto3
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version='s3v4') # Explicitly set v4 signature
            )
            self.s3_resource = boto3.resource(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION_NAME,
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version='s3v4')
            )
            logger.info("S3 client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
            self.s3_resource = None


    def check_s3_connection(self):
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot check connection.")
            return False
        try:
            self.s3_client.list_buckets() # Simple operation to check connectivity and credentials
            logger.info("S3 connection successful.")
            return True
        except NoCredentialsError:
            logger.error("S3 connection failed: Credentials not available.")
            return False
        except ClientError as e:
            logger.error(f"S3 connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"S3 connection failed with an unexpected error: {e}")
            return False

    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        if not self.s3_resource or not self.s3_client:
            logger.error(f"S3 client not initialized. Cannot create bucket {bucket_name}.")
            return False
        try:
            # Check if bucket exists using head_bucket (more efficient than listing)
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' already exists.")
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404: # Bucket does not exist
                logger.info(f"Bucket '{bucket_name}' not found. Creating...")
                try:
                    # For MinIO, region usually doesn't matter for bucket creation.
                    # For AWS S3, you might need to specify LocationConstraint for regions other than us-east-1.
                    if settings.S3_ENDPOINT_URL and "amazonaws.com" in settings.S3_ENDPOINT_URL and settings.S3_REGION_NAME != "us-east-1":
                        self.s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.S3_REGION_NAME}
                        )
                    else:
                        self.s3_client.create_bucket(Bucket=bucket_name)
                    logger.info(f"Bucket '{bucket_name}' created successfully.")
                except ClientError as e_create:
                    logger.error(f"Could not create bucket '{bucket_name}': {e_create}")
                    return False
            else: # Some other error
                logger.error(f"Error checking bucket '{bucket_name}': {e}")
                return False
        return True

    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: Optional[str] = None
    ) -> Optional[str]:
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot upload file.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 service not configured")

        if object_name is None:
            object_name = file.filename

        try:
            # Reset file pointer to the beginning before reading
            await file.seek(0)
            self.s3_client.upload_fileobj(file.file, bucket_name, object_name)
            logger.info(f"File '{file.filename}' uploaded to '{bucket_name}/{object_name}'.")
            # Construct the S3 object URL (this might vary based on S3 provider/MinIO setup)
            # For MinIO, it's often endpoint_url/bucket_name/object_name
            # For AWS S3, it's s3://bucket_name/object_name or https://bucket.s3.region.amazonaws.com/object
            # For now, just return the object_name or a relative path
            return f"s3://{bucket_name}/{object_name}" # A conceptual path
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not upload file: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during file upload: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during file upload.")


    def generate_presigned_url(self, bucket_name: str, object_name: str, expiration: int = 3600) -> Optional[str]:
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot generate presigned URL.")
            return None
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

# Instantiate the service for easy import
s3_service = S3Service()

# Function to be called at application startup to ensure buckets exist
def init_s3_buckets():
    if s3_service.check_s3_connection():
        s3_service.create_bucket_if_not_exists(settings.S3_BUCKET_NAME_DATASETS)
        s3_service.create_bucket_if_not_exists(settings.S3_BUCKET_NAME_RESULTS)
    else:
        logger.error("S3 connection failed. Buckets will not be initialized.")