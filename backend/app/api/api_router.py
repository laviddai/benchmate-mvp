# backend/app/api/api_router.py
from fastapi import APIRouter

from app.api.endpoints import (
    user_router,
    project_router,
    dataset_router, # Make sure this is imported
    analysis_run_router,
    volcano_plot_tool_router
)

api_router = APIRouter()

api_router.include_router(user_router.router, prefix="/users", tags=["Users"])
api_router.include_router(project_router.router, prefix="/projects", tags=["Projects"])
api_router.include_router(dataset_router.router, prefix="/datasets", tags=["Datasets"]) # <<< THIS LINE
api_router.include_router(analysis_run_router.router, prefix="/analysis-runs", tags=["Analysis Runs"])
api_router.include_router(
    volcano_plot_tool_router.router,
    prefix="/analyses/volcano-plot",
    tags=["Analyses - Volcano Plot Tool"]
)