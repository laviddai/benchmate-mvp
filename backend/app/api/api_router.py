# backend/app/api/api_router.py

from fastapi import APIRouter

# --- Import from the new, organized locations ---
from app.api.endpoints.core import (
    user_router,
    project_router,
    dataset_router,
    analysis_run_router,
    file_router
)
from app.api.endpoints.tools.bulk_rna_seq import (
    volcano_plot_router,
    pca_plot_router,
    heatmap_router
)
# --- NEW: Import the imaging routers ---
from app.api.endpoints.tools.imaging.filters import gaussian_blur_router
from app.api.endpoints.tools.imaging.segmentation import auto_threshold_router


api_router = APIRouter()

# --- Include the core routers ---
api_router.include_router(user_router.router, prefix="/users", tags=["Users"])
api_router.include_router(project_router.router, prefix="/projects", tags=["Projects"])
api_router.include_router(dataset_router.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(analysis_run_router.router, prefix="/analysis-runs", tags=["Analysis Runs"])
api_router.include_router(file_router.router, prefix="/files", tags=["Files"])


# --- Include the tool-specific submission endpoints ---

# --- Start of Bulk RNA Seq ---
api_router.include_router(
    volcano_plot_router.router,
    prefix="/analyses/bulk-rna-seq/volcano-plot",
    tags=["Analyses - Bulk RNA-Seq"]
)
api_router.include_router(
    pca_plot_router.router,
    prefix="/analyses/bulk-rna-seq/pca-plot",
    tags=["Analyses - Bulk RNA-Seq"]
)
api_router.include_router(
    heatmap_router.router,
    prefix="/analyses/bulk-rna-seq/heatmap",
    tags=["Analyses - Bulk RNA-Seq"]
)
# --- End of Bulk RNA Seq ---

# --- Start of Imaging ---
api_router.include_router(
    gaussian_blur_router.router,
    prefix="/analyses/imaging/filters/gaussian-blur",
    tags=["Analyses - Imaging"]
)
# --- NEW: Add the auto-threshold router ---
api_router.include_router(
    auto_threshold_router.router,
    prefix="/analyses/imaging/segmentation/auto-threshold",
    tags=["Analyses - Imaging"]
)
# --- End of Imaging ---

# Example for the future: When we add a plot tool, its router will be added here.
# from app.api.endpoints.tools.bulk_rna_seq import pca_plot_router
# api_router.include_router(
#     pca_plot_router.router, 
#     prefix="/analyses/pca-plot", 
#     tags=["Analyses - PCA Plot"]
# )