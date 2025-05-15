# backend/app/utils/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano-processor.py

import io
import base64
import pandas as pd

from backend.app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano import VolcanoParams
from backend.app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano_processor import (
    load_data,
    preprocess_data,
    plot_volcano
)

def fig_to_base64(fig) -> str:
    """
    Convert a Matplotlib Figure to a data URI (PNG, base64-encoded).
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"

def run(file_obj, params: VolcanoParams, config: dict) -> dict:
    """
    Unified entry point for the volcano tool.

    Arguments:
      file_obj: an uploaded file-like object
      params: a VolcanoParams instance with user-supplied mappings & thresholds
      config: dict from volcano.yaml with graph settings & defaults

    Returns:
      dict with keys "plot_image" (data-URI) and "summary" (stats)
    """
    # 1) Load into DataFrame
    ext = getattr(file_obj, "filename", "").split(".")[-1]
    df = load_data(file_obj.file if hasattr(file_obj, "file") else file_obj, f".{ext}")

    # 2) Build mapping dict from params (only non-None)
    mapping = {
        **({"gene": params.gene_col} if params.gene_col else {}),
        **({"log2fc": params.log2fc_col} if params.log2fc_col else {}),
        **({"pvalue": params.pvalue_col} if params.pvalue_col else {}),
    }

    # 3) Preprocess
    df_proc = preprocess_data(df, mapping=mapping)

    # 4) Plot
    fig = plot_volcano(
        df=df_proc,
        label_genes=params.label_top_n and df_proc.nlargest(params.label_top_n, "composite_score")["gene"].tolist() or [],
        title=config["graph"]["title"],
        xlabel=config["graph"]["xlabel"],
        ylabel=config["graph"]["ylabel"],
        x_col=params.log2fc_col or config["expected_columns"]["log2fc"],
        y_col=params.pvalue_col or config["expected_columns"]["pvalue"],
        gene_col=params.gene_col or config["expected_columns"]["gene"],
        fc_thresh=params.fold_change_threshold,
        pval_thresh=params.p_value_threshold,
        legend_title=config.get("legend", {}).get("title", "Regulation"),
        show_threshold_line=config.get("layout", {}).get("show_threshold_line", True),
        footer_text=config.get("layout", {}).get("footer_text", ""),
    )

    # 5) Encode and return
    return {
        "plot_image": fig_to_base64(fig),
        "summary": {"n_genes": len(df_proc)},
    }
