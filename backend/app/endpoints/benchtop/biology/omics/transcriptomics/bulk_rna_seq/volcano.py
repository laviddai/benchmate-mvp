# backend/app/endpoints/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.py

import os
from io import BytesIO

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.volcano import VolcanoParams, VolcanoResponse
from app.utils.config_loader import load_yaml_config
from app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano_processor import (
    load_data,
    preprocess_data,
    plot_volcano,
    fig_to_base64
)

router = APIRouter()

@router.post(
    "/run",
    response_model=VolcanoResponse,
    summary="Run Volcano Plot Tool",
    description=(
        "Accepts an uploaded file along with optional column‐mapping form fields. "
        "Returns a base64‐encoded PNG and summary statistics."
    ),
)
async def run_volcano(
    file: UploadFile = File(...),
    pvalue_col: str = Form(None),
    log2fc_col: str = Form(None),
    gene_col: str = Form(None),
):
    """
    API endpoint to process a volcano plot tool.
    """
    # 1. Validate form fields via Pydantic
    params = VolcanoParams(
        pvalue_col=pvalue_col,
        log2fc_col=log2fc_col,
        gene_col=gene_col,
    )

    # 2. Read & parse the uploaded file
    try:
        contents = await file.read()
        stream = BytesIO(contents)
        _, ext = os.path.splitext(file.filename)
        df = load_data(stream, ext.lower())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load file: {e}")

    # 3. Preprocess, applying any user‐provided mappings
    try:
        mapping = params.dict(exclude_none=True) or None
        df_processed = preprocess_data(df, mapping=mapping)
    except ValueError as ve:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Missing required columns",
                "details": str(ve),
                "available_columns": df.columns.tolist(),
            },
        )

    # 4. Load plot config
    config = load_yaml_config(
        "benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.yaml"
    )

    # 5. Generate the volcano figure
    fig = plot_volcano(
        df=df_processed,
        label_genes=[],
        title=config.get("graph", {}).get("title", "Volcano Plot"),
        xlabel=config.get("graph", {}).get("xlabel", "Log2 Fold Change"),
        ylabel=config.get("graph", {}).get("ylabel", "-Log10(P-value)"),
        x_col=params.log2fc_col or config["expected_columns"].get("log2fc", "log2foldchange"),
        y_col=params.pvalue_col or config["expected_columns"].get("pvalue", "pvalue"),
        gene_col=params.gene_col or config["expected_columns"].get("gene", "gene"),
        fc_thresh=config.get("thresholds", {}).get("log2fc", 1.0),
        pval_thresh=config.get("thresholds", {}).get("pvalue", 0.05),
        legend_title=config.get("legend", {}).get("title", "Regulation"),
        show_threshold_line=config.get("layout", {}).get("show_threshold_line", True),
        footer_text=config.get("layout", {}).get("footer_text", ""),
    )

    # 6. Build a minimal summary
    summary_stats = {"n_genes": df_processed.shape[0]}

    # 7. Return JSON with a data‐URI plot and stats
    return {"plot_image": fig_to_base64(fig), "summary": summary_stats}
