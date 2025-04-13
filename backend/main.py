# FastAPI application entry point and mounting endpoint: backend/main.py

from fastapi import FastAPI
from backend.app.endpoints.benchtop.biology.omics.transcriptomics.bulk_rna_seq import volcano

app = FastAPI(title="BenchMate Backend API")

# Include the volcano plot endpoint router, mounting it at a dedicated path.
app.include_router(
    volcano.router,
    prefix="/api/benchtop/biology/omics/transcriptomics/bulk-rna-seq",
    tags=["Volcano Plot"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
