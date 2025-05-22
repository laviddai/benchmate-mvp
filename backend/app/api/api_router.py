# backend/app/api/api_router.py
from fastapi import APIRouter

from app.api.endpoints import user_router, project_router, dataset_router # Import your endpoint routers
# from app.api.endpoints import volcano_router # Your existing one, if you move it here

api_router = APIRouter()

# Include User routes
api_router.include_router(user_router.router, prefix="/users", tags=["Users"])

# Include Project routes
api_router.include_router(project_router.router, prefix="/projects", tags=["Projects"])

#Include Datasets routes
api_router.include_router(dataset_router.router, prefix="/datasets", tags=["Datasets"])

# Include Volcano Plot routes (example, if you refactor its location)
# from app.endpoints.benchtop.biology.omics.transcriptomics.bulk_rna_seq import volcano as volcano_endpoint_module
# api_router.include_router(
#     volcano_endpoint_module.router, # Assuming 'router' is the APIRouter instance in that file
#     prefix="/analyses/volcano", # Example new prefix
#     tags=["Analyses - Volcano Plot"]
# )