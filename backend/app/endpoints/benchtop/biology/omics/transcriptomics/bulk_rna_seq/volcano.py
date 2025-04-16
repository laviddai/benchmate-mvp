# backend/app/endpoints/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.py

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from io import BytesIO
import os

# Import the config loader and volcano processor functions.
from backend.app.utils.config_loader import load_yaml_config
from backend.app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano_processor import (
    load_data, preprocess_data, plot_volcano, fig_to_base64
)

router = APIRouter()

@router.post("/run", summary="Run Volcano Plot Tool")
async def run_volcano(
    file: UploadFile = File(...),
    pvalue_col: str = Form(None),
    log2fc_col: str = Form(None),
    gene_col: str = Form(None)
):
    """
    API endpoint to process a volcano plot tool.
    Accepts an uploaded file and optional column mapping overrides.
    Returns a JSON with a base64-encoded plot and summary statistics.
    """
    try:
        # Read file content as bytes.
        contents = await file.read()
        file_stream = BytesIO(contents)
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()

        # Load data using the processor function.
        df = load_data(file_stream, ext)
        
        # Create mapping from form parameters if provided.
        mapping = {}
        if pvalue_col:
            mapping["pvalue"] = pvalue_col
        if log2fc_col:
            mapping["log2fc"] = log2fc_col
        if gene_col:
            mapping["gene"] = gene_col
        
        # Preprocess the data. Mapping is applied if non-empty.
        try:
            df_processed = preprocess_data(df, mapping=mapping if mapping else None)
        except ValueError as ve:
            # Return an informative error response so the frontend can ask the user for mapping.
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Missing required columns",
                    "details": str(ve),
                    "available_columns": df.columns.tolist()
                }
            )
        
        # Load volcano tool configuration from YAML.
        # Adjust the path if necessary (here, relative to the project root).
        config = load_yaml_config("backend/app/config/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.yaml")
        
        # Generate the volcano plot.
        fig = plot_volcano(
            df=df_processed,
            label_genes=[],  # Optionally, allow labeling genes.
            title=config.get("graph", {}).get("title", "Volcano Plot"),
            xlabel="Log2 Fold Change",
            ylabel="-Log10(P-value)",
            x_col=config.get("expected_columns", {}).get("log2fc", "log2foldchange"),
            y_col=config.get("expected_columns", {}).get("pvalue", "pvalue"),
            gene_col=config.get("expected_columns", {}).get("gene", "gene"),
            fc_thresh=config.get("thresholds", {}).get("log2fc", 1.0),
            pval_thresh=config.get("thresholds", {}).get("pvalue", 0.05),
            legend_title=config.get("legend", {}).get("title", "Regulation"),
            colors=config.get("colors", {"up": "red", "down": "blue", "neutral": "gray"}),
            legend_labels=config.get("legend", {}).get("labels", {"up": "Up", "down": "Down", "neutral": "Neutral"}),
            show_grid=config.get("layout", {}).get("show_grid", True),
            legend_position=config.get("legend", {}).get("position", "best"),
            figsize=(config.get("layout", {}).get("plot_width", 8), config.get("layout", {}).get("plot_height", 6)),
            xlim=(config.get("axis", {}).get("x_min", -5), config.get("axis", {}).get("x_max", 5)),
            ylim=(config.get("axis", {}).get("y_min", 0), config.get("axis", {}).get("y_max", 10)),
            log_scale_y=config.get("axis", {}).get("log_scale_y", False),
            show_threshold_line=True,
            footer_text=None
        )

        # Convert the Matplotlib figure to base64
        plot_base64 = fig_to_base64(fig)

        # Prepare response
        response = {
            "plot_image": plot_base64,
            "summary": {
                "total_genes": len(df),
                "processed_genes": len(df_processed)
            },
            "config": config
        }

        return JSONResponse(status_code=200, content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
