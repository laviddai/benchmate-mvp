# backend/main.py
from fastapi import FastAPI
from app.api.api_router import api_router # Import the main API router
from app.core.config import settings # If you need settings for app config

# Potentially configure CORS if your frontend is on a different domain/port during dev
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BenchMate Backend API",
    # openapi_url=f"{settings.API_V1_STR}/openapi.json" # Example if you add API versioning
)

# CORS (Cross-Origin Resource Sharing)
# Allows your frontend (e.g., localhost:3000) to make requests to your backend (e.g., localhost:8000)
# Adjust origins as needed, "*" is permissive for development.
# For production, specify exact origins.
origins = [
    "http://localhost:3000", # Your React frontend
    "http://localhost",      # Sometimes needed
    # Add your deployed frontend URL here later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# Include your main API router
# All routes from user_router and project_router will be prefixed with /api
app.include_router(api_router, prefix="/api")

# You can still include other routers directly if needed,
# but centralizing in api_router is cleaner.
# For example, if you keep the volcano plot separate for now:
# from app.endpoints.benchtop.biology.omics.transcriptomics.bulk_rna_seq import volcano as volcano_endpoint_module
# app.include_router(
#    volcano_endpoint_module.router,
#    prefix="/api/benchtop/biology/omics/transcriptomics/bulk-rna-seq", # Keep existing prefix
#    tags=["Volcano Plot - Legacy"] # Or just "Volcano Plot"
#)

if __name__ == "__main__":
    import uvicorn
    # Note: When running with Docker, the CMD in Dockerfile usually starts Uvicorn.
    # This __main__ block is more for direct execution (e.g., python backend/main.py).
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)