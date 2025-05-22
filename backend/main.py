# backend/main.py
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Ensure this is imported

from app.api.api_router import api_router
from app.core.config import settings
from app.services import init_s3_buckets # <<< IMPORT NEW FUNCTION

logging.basicConfig(
    stream=sys.stdout, # Log to standard output
    level=logging.INFO, # Log INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BenchMate Backend API",
    # openapi_url=f"{settings.API_V1_STR}/openapi.json" # If you add API versioning
)

# Startup event handler
@app.on_event("startup")
async def startup_event():
    print("Application startup: Initializing S3 buckets...") # For logging
    init_s3_buckets()
    print("S3 bucket initialization attempt complete.")


# CORS (Cross-Origin Resource Sharing)
origins = [
    "http://localhost:3000",
    "http://localhost",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# If you still have the volcano endpoint here:
#from app.endpoints.benchtop.biology.omics.transcriptomics.bulk_rna_seq import volcano as volcano_endpoint_module
#app.include_router(
#    volcano_endpoint_module.router,
#    prefix="/api/benchtop/biology/omics/transcriptomics/bulk-rna-seq",
#    tags=["Volcano Plot - Legacy"]
#)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)