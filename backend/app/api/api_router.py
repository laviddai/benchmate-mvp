# backend/app/api/api_router.py
from fastapi import APIRouter

# --- Import from the new, organized locations ---
from app.api.endpoints.core import (
    user_router, 
    project_router, 
    dataset_router, 
    file_router, 
    analysis_run_router
)
from app.api.endpoints.tools.bulk_rna_seq import volcano_plot_router

api_router = APIRouter()

# --- Include the core routers ---
# These handle the main data models of the application.
api_router.include_router(user_router.router, prefix="/users", tags=["Users"])
api_router.include_router(project_router.router, prefix="/projects", tags=["Projects"])
api_router.include_router(dataset_router.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(file_router.router, prefix="/files", tags=["Files"])
api_router.include_router(analysis_run_router.router, prefix="/analysis-runs", tags=["Analysis Runs"])


# --- Include the tool-specific submission endpoints ---
# This section will grow as we add more analysis tools.
api_router.include_router(
    volcano_plot_router.router, 
    prefix="/analyses/volcano-plot", 
    tags=["Analyses - Volcano Plot"]
)

# Example for the future: When we add a PCA plot tool, its router will be added here.
# from app.api.endpoints.tools.bulk_rna_seq import pca_plot_router
# api_router.include_router(
#     pca_plot_router.router, 
#     prefix="/analyses/pca-plot", 
#     tags=["Analyses - PCA Plot"]
# )