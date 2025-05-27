# backend/app/services/s3_service.py
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException, status
import logging
from typing import Optional, BinaryIO
import io

from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        if not all([settings.S3_ENDPOINT_URL, settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY]):
            logger.warning("S3 service is not fully configured. Some operations might fail.")
            self.s3_client_internal = None # For internal operations
            # self.s3_resource = None # Not strictly needed if using client methods
            return

        try:
            # This config is for path-style addressing, crucial for MinIO
            self._s3_config = Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            )

            # Client for backend-to-MinIO communication (within Docker network)
            self.s3_client_internal = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL, # e.g., http://minio:9000
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION_NAME,
                use_ssl=settings.S3_USE_SSL,
                config=self._s3_config
            )
            logger.info(f"S3 internal client initialized. Endpoint: {settings.S3_ENDPOINT_URL}")

        except Exception as e:
            logger.error(f"Failed to initialize S3 internal client: {e}")
            self.s3_client_internal = None
    
    # Make sure other methods use self.s3_client_internal
    def check_s3_connection(self):
        if not self.s3_client_internal: # Check internal client
            logger.error("S3 internal client not initialized. Cannot check connection.")
            return False
        try:
            self.s3_client_internal.list_buckets()
            logger.info("S3 connection successful via list_buckets().")
            return True
        # ... (rest of check_s3_connection with self.s3_client_internal) ...
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
        if not self.s3_client_internal: # Check internal client
            logger.error(f"S3 internal client not initialized. Cannot create bucket {bucket_name}.")
            return False
        try:
            self.s3_client_internal.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' already exists.")
        # ... (rest of create_bucket_if_not_exists with self.s3_client_internal) ...
        except ClientError as e:
            error_code_str = e.response.get('Error', {}).get('Code')
            if error_code_str and str(error_code_str) == '404': # Bucket does not exist
                logger.info(f"Bucket '{bucket_name}' not found. Creating...")
                try:
                    if settings.S3_ENDPOINT_URL and "amazonaws.com" in settings.S3_ENDPOINT_URL and settings.S3_REGION_NAME != "us-east-1":
                        self.s3_client_internal.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.S3_REGION_NAME}
                        )
                    else:
                        self.s3_client_internal.create_bucket(Bucket=bucket_name)
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
        if not self.s3_client_internal: # Check internal client
            logger.error("S3 internal client not initialized. Cannot upload file.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 service not configured")
        # ... (rest of upload_file with self.s3_client_internal) ...
        if object_name is None:
            object_name = file.filename 

        try:
            await file.seek(0) 
            self.s3_client_internal.upload_fileobj(file.file, bucket_name, object_name) 
            logger.info(f"File '{file.filename}' uploaded to '{bucket_name}/{object_name}'.")
            return f"s3://{bucket_name}/{object_name}"
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not upload file to S3: {e.response.get('Error',{}).get('Message','Unknown S3 error')}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during file upload: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during file upload: {str(e)}")


    def download_file_to_buffer(self, bucket_name: str, object_key: str) -> Optional[io.BytesIO]:
        if not self.s3_client_internal: # Check internal client
            logger.error("S3 internal client not initialized. Cannot download file.")
            return None
        # ... (rest of download_file_to_buffer with self.s3_client_internal) ...
        buffer = io.BytesIO()
        try:
            self.s3_client_internal.download_fileobj(bucket_name, object_key, buffer)
            buffer.seek(0)
            logger.info(f"File '{object_key}' from bucket '{bucket_name}' downloaded to in-memory buffer.")
            return buffer
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404': 
                logger.error(f"File not found in S3: s3://{bucket_name}/{object_key}")
            else:
                logger.error(f"Failed to download file from S3 (s3://{bucket_name}/{object_key}): {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during S3 file download (s3://{bucket_name}/{object_key}): {e}")
            return None


    def generate_presigned_url(self, bucket_name: str, object_key: str, expiration: int = 3600, http_method: str = 'GET') -> Optional[str]:
        """
        Generates a presigned URL for an S3 object using the public-facing endpoint.
        """
        # Determine the endpoint URL to use for presigning
        # This should be the URL the client/browser will use to access MinIO/S3
        presigning_endpoint_url = settings.S3_PUBLIC_ENDPOINT_URL or settings.S3_ENDPOINT_URL
        if not presigning_endpoint_url:
            logger.error("No S3 endpoint URL (neither public nor internal) configured for presigning.")
            return None
        
        if not all([settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY]):
            logger.error("S3 access key or secret key not configured for presigning.")
            return None

        # Create a temporary S3 client specifically for presigning, configured with the public endpoint
        # and the same path-style config.
        try:
            presign_client = boto3.client(
                "s3",
                endpoint_url=presigning_endpoint_url, # Use public endpoint
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION_NAME,
                use_ssl=settings.S3_USE_SSL, # Should match how public endpoint is accessed
                config=self._s3_config, # Reuse the same config for s3v4 and path_style
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client for presigning: {e}")
            return None

        client_method_action = None
        if http_method.upper() == 'GET':
            client_method_action = 'get_object'
        elif http_method.upper() == 'PUT':
            client_method_action = 'put_object'
        else:
            logger.error(f"Unsupported HTTP method '{http_method}' for presigned URL generation.")
            return None

        try:
            url = presign_client.generate_presigned_url(
                ClientMethod=client_method_action,
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            # The URL generated by boto3 will already use the presigning_endpoint_url's host.
            # So, no need to manually replace minio:9000 with localhost:9000 later IF
            # S3_PUBLIC_ENDPOINT_URL is correctly set to http://localhost:9000
            logger.info(f"Generated presigned URL (using {presigning_endpoint_url}) for {http_method.upper()} s3://{bucket_name}/{object_key}")
            return url
        except ClientError as e:
            logger.error(f"ClientError generating presigned URL for s3://{bucket_name}/{object_key} using endpoint {presigning_endpoint_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL for s3://{bucket_name}/{object_key} using endpoint {presigning_endpoint_url}: {e}")
            return None

s3_service = S3Service()

def init_s3_buckets():
    if s3_service.check_s3_connection(): # This will use s3_client_internal
        s3_service.create_bucket_if_not_exists(settings.S3_BUCKET_NAME_DATASETS)
        s3_service.create_bucket_if_not_exists(settings.S3_BUCKET_NAME_RESULTS)
    else:
        logger.error("S3 connection failed. Buckets will not be initialized.")