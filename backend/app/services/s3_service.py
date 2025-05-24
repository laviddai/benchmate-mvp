# backend/app/services/s3_service.py
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException, status
import logging
from typing import Optional, BinaryIO # <<< ADD BinaryIO
import io # <<< ADD io

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
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION_NAME,
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version='s3v4')
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
        # ... (existing code)
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot check connection.")
            return False
        try:
            self.s3_client.list_buckets() 
            logger.info("S3 connection successful via list_buckets().") # Added more detail
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
        # ... (existing code)
        if not self.s3_resource or not self.s3_client:
            logger.error(f"S3 client not initialized. Cannot create bucket {bucket_name}.")
            return False
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' already exists.")
        except ClientError as e:
            error_code_str = e.response.get('Error', {}).get('Code')
            if error_code_str and str(error_code_str) == '404': # Bucket does not exist
                logger.info(f"Bucket '{bucket_name}' not found. Creating...")
                try:
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
            else: 
                logger.error(f"Error checking bucket '{bucket_name}': {e}")
                return False
        return True


    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: Optional[str] = None
    ) -> Optional[str]:
        # ... (existing code)
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot upload file.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 service not configured")

        if object_name is None:
            object_name = file.filename 

        try:
            await file.seek(0) 
            self.s3_client.upload_fileobj(file.file, bucket_name, object_name) 
            logger.info(f"File '{file.filename}' uploaded to '{bucket_name}/{object_name}'.")
            return f"s3://{bucket_name}/{object_name}"
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not upload file to S3: {e.response.get('Error',{}).get('Message','Unknown S3 error')}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during file upload: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during file upload: {str(e)}")

    # --- NEW METHOD ---
    def download_file_to_buffer(self, bucket_name: str, object_key: str) -> Optional[io.BytesIO]:
        """
        Downloads a file from S3/MinIO into an in-memory BytesIO buffer.
        Returns the BytesIO buffer or None if download fails.
        """
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot download file.")
            return None
        
        buffer = io.BytesIO()
        try:
            self.s3_client.download_fileobj(bucket_name, object_key, buffer)
            buffer.seek(0)  # Reset buffer's cursor to the beginning for reading
            logger.info(f"File '{object_key}' from bucket '{bucket_name}' downloaded to in-memory buffer.")
            return buffer
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"File not found in S3: s3://{bucket_name}/{object_key}")
            else:
                logger.error(f"Failed to download file from S3 (s3://{bucket_name}/{object_key}): {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during S3 file download (s3://{bucket_name}/{object_key}): {e}")
            return None
    # --- END NEW METHOD ---

    def generate_presigned_url(self, bucket_name: str, object_name: str, expiration: int = 3600) -> Optional[str]:
        # ... (existing code)
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

s3_service = S3Service()

def init_s3_buckets():
    # ... (existing code)
    if s3_service.check_s3_connection():
        s3_service.create_bucket_if_not_exists(settings.S3_BUCKET_NAME_DATASETS)
        s3_service.create_bucket_if_not_exists(settings.S3_BUCKET_NAME_RESULTS)
    else:
        logger.error("S3 connection failed. Buckets will not be initialized.")