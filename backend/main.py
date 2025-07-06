# backend/main.py

import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_router import api_router
from app.core.config import settings
from app.db.session import engine
from app.db import base
from app.services.s3_service import init_s3_buckets
from app.services.imagej_service import init_imagej_gateway

# Configure logging
# To see logs from the application in the console
logging.basicConfig(
    stream=sys.stdout, # Log to standard output
    level=logging.INFO, # Log INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create all database tables (if they don't exist)
# This is simple for development but for production, Alembic migrations are preferred.
# Base.metadata.create_all(bind=engine) # This is handled by Alembic in docker-compose

app = FastAPI(
    title="BenchMate API",
    description="Backend services for the BenchMate platform, including BenchTop analytical workbench.",
    version="0.2.0",
    # openapi_url=f"{settings.API_V1_STR}/openapi.json" # If you add API versioning
)

# Startup event handler
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    """
    logger.info("Application startup: Initializing services...")
    try:
        # Initialize S3 buckets
        init_s3_buckets()
        logger.info("S3 buckets initialized successfully.")

        # Eagerly initialize the ImageJ gateway
        # This will start the JVM and catch any setup errors early.
        init_imagej_gateway()
        logger.info("ImageJ gateway initialized successfully.")

    except Exception as e:
        logger.critical(f"A critical error occurred during startup: {e}", exc_info=True)
        # Depending on the desired behavior, you might want the app to exit
        # if a critical service like ImageJ fails to start.
        # For now, we log it as critical and allow the app to continue running,
        # though imaging endpoints will fail.

# CORS (Cross-Origin Resource Sharing)
# This allows the frontend (running on a different origin, e.g., localhost:3000)
# to communicate with the backend API.
origins = [
    "http://localhost",
    "http://localhost:3000",
    # Add other origins as needed (e.g., your production frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# Include the main API router
app.include_router(api_router, prefix="/api")

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing basic information about the API.
    """
    return {"message": "Welcome to the BenchMate API. See /docs for documentation."}