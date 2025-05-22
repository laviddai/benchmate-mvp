# backend/app/services/s3_service.py
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile, HTTPException, status # Ensure HTTPException and status are imported
import logging
from typing import Optional

from app.core.config import settings

# Get a logger instance for this module
logger = logging.getLogger(__name__) # Use __name__ for the logger name

class S3Service:
    def __init__(self):
        """
        Initializes the S3 client and resource.
        Logs warnings if S3 configuration is incomplete.
        """
        # Check if all necessary S3 settings are provided
        if not all([
            settings.S3_ENDPOINT_URL,
            settings.S3_ACCESS_KEY,
            settings.S3_SECRET_KEY,
            settings.S3_BUCKET_NAME_DATASETS, # Added bucket names to the check
            settings.S3_BUCKET_NAME_RESULTS
        ]):
            logger.warning(
                "S3 service is not fully configured (endpoint, access key, secret key, or bucket names might be missing). "
                "File operations might fail."
            )
            self.s3_client = None
            self.s3_resource = None
            return # Exit initialization if not fully configured

        try:
            # Initialize boto3 S3 client
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION_NAME,
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version='s3v4')
            )
            # Initialize boto3 S3 resource (useful for bucket operations)
            self.s3_resource = boto3.resource(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION_NAME,
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version='s3v4')
            )
            logger.info("S3 client and resource initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client/resource: {e}")
            self.s3_client = None
            self.s3_resource = None

    def check_s3_connection(self) -> bool:
        """
        Checks the connectivity to the S3 service and logs the outcome.
        Returns True if connection is successful, False otherwise.
        """
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot check connection.")
            return False
        try:
            self.s3_client.list_buckets() # A simple operation to test connection and credentials
            logger.info("S3 connection successful via list_buckets().")
            return True
        except NoCredentialsError:
            logger.error("S3 connection failed: Credentials not available or incorrect.")
            return False
        except ClientError as e:
            logger.error(f"S3 connection failed (ClientError): {e.response.get('Error',{}).get('Message','Unknown S3 ClientError')}")
            return False
        except Exception as e:
            logger.error(f"S3 connection failed with an unexpected error: {e}")
            return False

    def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """
        Creates an S3 bucket if it does not already exist.
        Logs the outcome.
        Returns True if bucket exists or was created, False on failure.
        """
        if not self.s3_client: # Changed from self.s3_resource for consistency with head_bucket
            logger.error(f"S3 client not initialized. Cannot create or check bucket '{bucket_name}'.")
            return False
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket '{bucket_name}' already exists.")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404' or error_code == 'NoSuchBucket': # Handle different error codes for "not found"
                logger.info(f"Bucket '{bucket_name}' not found. Creating...")
                try:
                    # For AWS S3, region needs to be specified for bucket creation
                    # if it's not us-east-1. MinIO typically ignores this.
                    if "amazonaws.com" in (settings.S3_ENDPOINT_URL or "") and settings.S3_REGION_NAME != "us-east-1":
                        self.s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': settings.S3_REGION_NAME}
                        )
                    else:
                        self.s3_client.create_bucket(Bucket=bucket_name)
                    logger.info(f"Bucket '{bucket_name}' created successfully.")
                except ClientError as e_create:
                    logger.error(f"Could not create bucket '{bucket_name}': {e_create.response.get('Error',{}).get('Message','Unknown S3 ClientError during create_bucket')}")
                    return False
            else: # Some other ClientError
                logger.error(f"Error checking bucket '{bucket_name}': {e.response.get('Error',{}).get('Message','Unknown S3 ClientError during head_bucket')}")
                return False
        except Exception as e_general: # Catch any other unexpected errors
            logger.error(f"Unexpected error checking or creating bucket '{bucket_name}': {e_general}")
            return False
        return True

    async def upload_file(
        self, file: UploadFile, bucket_name: str, object_name: Optional[str] = None
    ) -> str: # Changed return type to str, as it should always return a path or raise error
        """
        Uploads a FastAPI UploadFile object to the specified S3 bucket.
        The method is async to allow for `await file.seek(0)`.
        Returns the S3 object path (s3://bucket/key) upon success.
        Raises HTTPException on failure.
        """
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot upload file.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 service is not configured or failed to initialize.")

        if object_name is None:
            object_name = file.filename  # Fallback, but router should provide a good name

        if not object_name: # Ensure object_name is not empty after fallback
            logger.error("Object name for S3 upload is empty.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name for S3 object is invalid or missing.")

        try:
            await file.seek(0)  # Crucial for re-reading UploadFile if it has been read before
            self.s3_client.upload_fileobj(
                file.file,      # Pass the actual file-like object (SpooledTemporaryFile)
                bucket_name,
                object_name
            )
            s3_path = f"s3://{bucket_name}/{object_name}"
            logger.info(f"File '{file.filename}' uploaded to '{s3_path}'.")
            return s3_path
        except ClientError as e:
            error_msg = e.response.get('Error',{}).get('Message','Unknown S3 ClientError during upload')
            logger.error(f"Failed to upload file '{file.filename}' to S3 ('{bucket_name}/{object_name}'): {error_msg} (Code: {e.response.get('Error',{}).get('Code')})")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not upload file to S3: {error_msg}")
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred during file upload of '{file.filename}' to '{bucket_name}/{object_name}': {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during file upload: {str(e)}")

    def generate_presigned_url(
        self, bucket_name: str, object_name: str, expiration: int = 3600
    ) -> Optional[str]:
        """
        Generates a presigned URL to allow temporary access to an S3 object.
        Returns the URL string or None on failure.
        """
        if not self.s3_client:
            logger.error("S3 client not initialized. Cannot generate presigned URL.")
            return None # Or raise an exception if this is a critical failure

        # Ensure object_name doesn't have the s3:// prefix if it was stored that way
        if object_name.startswith(f"s3://{bucket_name}/"):
            actual_object_key = object_name.split(f"s3://{bucket_name}/", 1)[1]
        else:
            actual_object_key = object_name

        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': actual_object_key},
                ExpiresIn=expiration  # Time in seconds for the URL to be valid
            )
            return response
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for '{bucket_name}/{actual_object_key}': {e.response.get('Error',{}).get('Message','Unknown S3 ClientError')}")
            return None
        except Exception as e_general:
            logger.error(f"Unexpected error generating presigned URL for '{bucket_name}/{actual_object_key}': {e_general}")
            return None

# --- Initialization ---
# Create a single, importable instance of the S3Service.
s3_service = S3Service()

# Function to be called at application startup to ensure buckets exist.
# This should be called after the S3Service instance is created and logger is available.
def init_s3_buckets():
    """
    Initializes S3 buckets defined in settings.
    Should be called during application startup.
    """
    if s3_service.s3_client and s3_service.check_s3_connection(): # Check if client was initialized
        # Create datasets bucket
        if settings.S3_BUCKET_NAME_DATASETS:
            s3_service.create_bucket_if_not_exists(settings.S3_BUCKET_NAME_DATASETS)
        else:
            logger.warning("S3_BUCKET_NAME_DATASETS is not configured. Skipping bucket creation.")

        # Create results bucket
        if settings.S3_BUCKET_NAME_RESULTS:
            s3_service.create_bucket_if_not_exists(settings.S3_BUCKET_NAME_RESULTS)
        else:
            logger.warning("S3_BUCKET_NAME_RESULTS is not configured. Skipping bucket creation.")
    else:
        logger.error(
            "S3 connection failed or S3 client not initialized. "
            "Buckets ('datasets', 'results') will not be automatically initialized."
        )