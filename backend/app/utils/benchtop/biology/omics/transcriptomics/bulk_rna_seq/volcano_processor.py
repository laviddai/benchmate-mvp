# backend/app/utils/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano_processor.py

import pandas as pd
import numpy as np # Assuming this was used by plot_volcano, add if missing
import matplotlib.pyplot as plt # Assuming this was used by plot_volcano, add if missing
import io
import base64
from typing import Optional, Any, Dict, List
import os

# Corrected import for VolcanoParams Pydantic schema
from app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano import VolcanoParams
# The functions load_data, preprocess_data, plot_volcano should be defined IN THIS FILE.
# So, no need to import them from itself.

# Ensure these functions are defined here as per your original XML structure:
# (I'm taking these from your original XML for volcano_processor.py)

def load_data(file_obj, ext):
    """
    Load data from a file object based on its extension.
    """
    if ext in ['.xls', '.xlsx']:
        return pd.read_excel(file_obj)
    else: # Assumes .csv, .tsv, or other text-based delimited files
        # For CSV/TSV, pandas can often infer delimiter, or you might need to specify
        try:
            return pd.read_csv(file_obj)
        except pd.errors.ParserError:
            # Try with tab delimiter if comma fails
            file_obj.seek(0) # Reset buffer for second attempt
            return pd.read_csv(file_obj, sep='\t')
        except Exception as e:
            raise ValueError(f"Failed to parse file with extension {ext}: {e}")


def find_column(df, expected_names_list: list, provided_name: Optional[str] = None):
    """
    Find a column in the DataFrame.
    1. Try the `provided_name` if given.
    2. Try case-insensitive match for `provided_name`.
    3. Iterate through `expected_names_list` (synonyms) with case-insensitive match.
    All column names in df are lowercased first for matching.
    """
    df_cols_lower = [str(col).lower() for col in df.columns]

    if provided_name:
        provided_name_lower = str(provided_name).lower()
        if provided_name_lower in df_cols_lower:
            # Find original casing
            for original_col in df.columns:
                if str(original_col).lower() == provided_name_lower:
                    return original_col
        # If exact (case-insensitive) provided_name not found, it will fall through to synonyms
    
    for name in expected_names_list:
        name_lower = str(name).lower()
        if name_lower in df_cols_lower:
            for original_col in df.columns:
                if str(original_col).lower() == name_lower:
                    return original_col
    return None


def preprocess_data(df: pd.DataFrame, mapping: dict, config: dict) -> pd.DataFrame:
    """
    Clean, map, and augment the DataFrame for downstream plotting.
    - Uses provided mapping or defaults from config for pvalue, log2fc, gene.
    - Computes -log10(p-value) and composite_score.
    """
    df_processed = df.copy()

    # Get expected column names from config (these are defaults/synonyms)
    expected_pvalue_cols = config.get("expected_columns", {}).get("pvalue_synonyms", ["pvalue", "p_value", "pval", "adj.pval", "fdr"])
    expected_log2fc_cols = config.get("expected_columns", {}).get("log2fc_synonyms", ["log2foldchange", "log2_fc", "logfc", "foldchange"])
    expected_gene_cols = config.get("expected_columns", {}).get("gene_synonyms", ["gene", "gene_symbol", "id", "geneid"])

    # Find actual column names using the mapping provided by user or defaults
    pval_col_actual = find_column(df_processed, expected_pvalue_cols, mapping.get("pvalue"))
    log2fc_col_actual = find_column(df_processed, expected_log2fc_cols, mapping.get("log2fc"))
    gene_col_actual = find_column(df_processed, expected_gene_cols, mapping.get("gene"))

    missing_required = []
    if not pval_col_actual: missing_required.append("p-value (e.g., 'pvalue', 'PValue', 'adj.P.Val')")
    if not log2fc_col_actual: missing_required.append("log2 fold change (e.g., 'logFC', 'log2FoldChange')")
    # Gene column is often optional for plotting, but good to have for labels
    if not gene_col_actual: print(f"Warning: Gene column not found or mapped. Gene labels might be unavailable.")


    if missing_required:
        raise ValueError(
            f"Missing required column(s) after attempting to map. Please ensure your file contains and you have mapped: {', '.join(missing_required)}. "
            f"Available columns in your file: {df_processed.columns.tolist()}"
        )

    # Ensure numeric types for calculation columns
    try:
        df_processed[log2fc_col_actual] = pd.to_numeric(df_processed[log2fc_col_actual])
        df_processed[pval_col_actual] = pd.to_numeric(df_processed[pval_col_actual])
    except ValueError as e:
        raise ValueError(f"Could not convert log2FC or P-value columns to numeric. Please check data. Error: {e}")

    # Compute -log10(p-value)
    # Add a small constant to p-values to avoid log(0) errors if p-values can be zero
    df_processed["_minus_log10_pvalue_"] = -np.log10(df_processed[pval_col_actual] + np.finfo(float).tiny)
    
    # Composite score (example: abs(log2FC) * -log10(p-value))
    df_processed["_composite_score_"] = np.abs(df_processed[log2fc_col_actual]) * df_processed["_minus_log10_pvalue_"]
    
    # Rename columns to standardized internal names for plotting function
    # This makes plot_volcano function simpler as it expects fixed column names.
    df_processed.rename(columns={
        log2fc_col_actual: "_INTERNAL_LOG2FC_",
        pval_col_actual: "_INTERNAL_PVALUE_", # Original pvalue
        gene_col_actual: "_INTERNAL_GENE_" # if gene_col_actual else keep as is
    }, inplace=True)
    
    return df_processed


def plot_volcano(
    df: pd.DataFrame, # Expects df from preprocess_data with internal column names
    params: VolcanoParams, # Pydantic model with thresholds, label_top_n
    config: dict # YAML config for colors, labels, layout
) -> plt.Figure:
    """
    Generate a volcano plot with classification and optional gene labels.
    Returns a Matplotlib Figure.
    Assumes df has columns: '_INTERNAL_LOG2FC_', '_minus_log10_pvalue_', '_INTERNAL_GENE_', '_composite_score_'
    """
    fig, ax = plt.subplots(figsize=(config.get("layout", {}).get("plot_width", 8), config.get("layout", {}).get("plot_height", 6)))

    # Define colors and labels from config or use defaults
    colors_cfg = config.get("colors", {"up": "red", "down": "blue", "neutral": "grey"})
    legend_cfg = config.get("legend", {"labels": {"up": "Upregulated", "down": "Downregulated", "neutral": "No Change"}, "title": "Regulation"})

    # Classify regulation based on thresholds from params
    df_plot = df.copy() # Avoid modifying the input DataFrame slice
    df_plot["regulation"] = "neutral"
    
    up_condition = (df_plot["_INTERNAL_LOG2FC_"] >= params.fold_change_threshold) & (df_plot["_INTERNAL_PVALUE_"] < params.p_value_threshold)
    down_condition = (df_plot["_INTERNAL_LOG2FC_"] <= -params.fold_change_threshold) & (df_plot["_INTERNAL_PVALUE_"] < params.p_value_threshold)
    
    df_plot.loc[up_condition, "regulation"] = "up"
    df_plot.loc[down_condition, "regulation"] = "down"

    # Scatter plot for each group
    for reg_status, group_df in df_plot.groupby("regulation"):
        ax.scatter(
            group_df["_INTERNAL_LOG2FC_"],
            group_df["_minus_log10_pvalue_"],
            label=legend_cfg.get("labels", {}).get(reg_status, reg_status.capitalize()),
            color=colors_cfg.get(reg_status, "grey"),
            alpha=0.7,
            s=20 # marker size
        )

    # Add threshold lines
    if config.get("layout", {}).get("show_threshold_line", True):
        ax.axhline(y=-np.log10(params.p_value_threshold), linestyle="--", color="black", linewidth=0.8)
        ax.axvline(x=params.fold_change_threshold, linestyle="--", color="black", linewidth=0.8)
        ax.axvline(x=-params.fold_change_threshold, linestyle="--", color="black", linewidth=0.8)

    # Label top N genes if requested and gene column exists
    if params.label_top_n > 0 and "_INTERNAL_GENE_" in df_plot.columns:
        # Select significant genes first
        significant_genes = df_plot[up_condition | down_condition]
        # Then from those, select top N by composite score
        genes_to_label_df = significant_genes.nlargest(params.label_top_n, "_composite_score_")
        for idx, row in genes_to_label_df.iterrows():
            ax.text(row["_INTERNAL_LOG2FC_"], row["_minus_log10_pvalue_"], str(row["_INTERNAL_GENE_"]), fontsize=8, alpha=0.9)
    
    # Axis labels and title from config or params
    graph_cfg = config.get("graph", {})
    ax.set_xlabel(graph_cfg.get("xlabel", "log2 Fold Change"))
    ax.set_ylabel(graph_cfg.get("ylabel", "-log10(P-value)"))
    ax.set_title(config.get("graph", {}).get("title", "Volcano Plot"))

    # Limits and scale from config
    axis_cfg = config.get("axis", {})
    if axis_cfg.get("x_min") is not None and axis_cfg.get("x_max") is not None:
        ax.set_xlim(axis_cfg["x_min"], axis_cfg["x_max"])
    if axis_cfg.get("y_min") is not None and axis_cfg.get("y_max") is not None:
        ax.set_ylim(axis_cfg["y_min"], axis_cfg["y_max"])
    if axis_cfg.get("log_scale_y", False): # Check if y-axis should be log scale (not typical for -log10 pval)
        ax.set_yscale("log")


    ax.grid(config.get("layout", {}).get("show_grid", True))
    ax.legend(title=legend_cfg.get("title", "Regulation"), loc=config.get("legend", {}).get("position", "best"))

    # Optional footer
    if config.get("layout", {}).get("add_footer", False) and config.get("layout", {}).get("footer_text"):
        fig.text(0.5, 0.01, config["layout"]["footer_text"], ha="center", fontsize=8, color="gray")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to prevent title/footer overlap
    return fig


def fig_to_base64(fig: plt.Figure) -> str:
    """
    Convert a Matplotlib Figure to a data URI (PNG, base64-encoded).
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150) # Added dpi
    plt.close(fig) # Close the figure to free memory
    buf.seek(0)
    data_bytes = buf.getvalue() # Use getvalue() for BytesIO
    base64_str = base64.b64encode(data_bytes).decode("utf-8")
    return f"data:image/png;base64,{base64_str}"

# This is the main entry point called by the Celery task
def run(file_obj: Any, params: VolcanoParams, config: dict) -> dict:
    """
    Unified entry point for the volcano tool.
    Arguments:
      file_obj: A file-like object (e.g., BytesIO from S3, or UploadFile.file)
                OR the MockFileWithFilename object from Celery worker.
      params: a VolcanoParams Pydantic model instance with user-supplied mappings & thresholds.
      config: dict from volcano.yaml with graph settings & defaults.
    Returns:
      dict with keys "plot_image" (data-URI) and "summary" (stats).
    """
    # 1) Determine file extension and get the actual file buffer
    if hasattr(file_obj, 'filename') and isinstance(file_obj.filename, str):
        file_extension = os.path.splitext(file_obj.filename)[1].lower()
    else:
        # Fallback if filename not available or not a string (e.g. direct BytesIO without name)
        # This part might need more robust handling if file_obj structure varies a lot
        file_extension = ".csv" # Default or try to get from params/config if possible
        print(f"Warning: Could not determine file extension from file_obj.filename. Assuming '{file_extension}'.")

    # Get the actual file-like object (buffer)
    actual_file_buffer = file_obj.file if hasattr(file_obj, 'file') else file_obj

    # Ensure buffer is at the beginning
    if hasattr(actual_file_buffer, 'seek'):
        actual_file_buffer.seek(0)

    # 2) Load data into DataFrame
    try:
        df = load_data(actual_file_buffer, file_extension)
    except Exception as e:
        # Log the error e
        raise ValueError(f"Failed to load data from input file. Ensure it's a valid CSV or Excel file. Error: {e}")

    # 3) Build mapping dict for preprocess_data
    # These come from the VolcanoParams Pydantic model passed in `params`
    mapping_for_preprocessing = {
        "pvalue": params.pvalue_col,
        "log2fc": params.log2fc_col,
        "gene": params.gene_col
    }
    # Filter out None values, as preprocess_data will use defaults from config if a mapping key is absent
    mapping_for_preprocessing = {k: v for k, v in mapping_for_preprocessing.items() if v is not None}

    # 4) Preprocess
    try:
        df_processed = preprocess_data(df, mapping=mapping_for_preprocessing, config=config)
    except ValueError as e: # Catch specific errors from preprocess_data (e.g., missing columns)
        # Log the error e
        raise e # Re-raise to be caught by Celery task's error handler

    # 5) Plot using the processed DataFrame and parameters
    # The plot_volcano function now takes the VolcanoParams object directly
    fig = plot_volcano(
        df=df_processed,
        params=params, # Pass the full Pydantic params object
        config=config
    )

    # 6) Encode plot to base64 and prepare summary
    plot_image_base64 = fig_to_base64(fig)
    summary_stats = {
        "total_genes_analyzed": len(df_processed),
        "significant_up": int(df_processed[
            (df_processed["_INTERNAL_LOG2FC_"] >= params.fold_change_threshold) &
            (df_processed["_INTERNAL_PVALUE_"] < params.p_value_threshold)
        ].shape[0]),
        "significant_down": int(df_processed[
            (df_processed["_INTERNAL_LOG2FC_"] <= -params.fold_change_threshold) &
            (df_processed["_INTERNAL_PVALUE_"] < params.p_value_threshold)
        ].shape[0]),
        "parameters_used": params.model_dump() # Include parameters used
    }
    
    return {
        "plot_image": plot_image_base64,
        "summary": summary_stats,
    }