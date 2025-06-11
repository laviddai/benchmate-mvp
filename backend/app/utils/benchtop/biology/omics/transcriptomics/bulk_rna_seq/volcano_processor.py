# backend/app/utils/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano_processor.py
import pandas as pd
import numpy as np
import io
import os
from typing import Any, Optional, Dict

# Import the Pydantic schema for type hinting and validation
from app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano import VolcanoParams

# --- Data Loading and Preprocessing (Largely Unchanged) ---

def load_data(file_obj: Any, ext: str) -> pd.DataFrame:
    """
    Load data from a file object based on its extension.
    """
    try:
        if ext == '.xlsx':
            return pd.read_excel(io.BytesIO(file_obj.read()))
        elif ext == '.csv':
            return pd.read_csv(io.BytesIO(file_obj.read()))
        else: # Assumes .tsv or other text-based delimited files
            # Try with comma delimiter first
            file_obj.seek(0)
            try:
                return pd.read_csv(io.BytesIO(file_obj.read()))
            except (pd.errors.ParserError, UnicodeDecodeError):
                # Try with tab delimiter if comma fails
                file_obj.seek(0)
                return pd.read_csv(io.BytesIO(file_obj.read()), sep='\t')
    except Exception as e:
        raise ValueError(f"Failed to load or parse the data file: {e}")

def find_column(df: pd.DataFrame, expected_names_list: list, provided_name: Optional[str] = None) -> Optional[str]:
    """
    Find a column in the DataFrame, trying provided name first, then synonyms. Case-insensitive.
    """
    df_cols_lower = {str(col).lower(): str(col) for col in df.columns}

    if provided_name:
        provided_name_lower = str(provided_name).lower()
        if provided_name_lower in df_cols_lower:
            return df_cols_lower[provided_name_lower]

    for name in expected_names_list:
        name_lower = str(name).lower()
        if name_lower in df_cols_lower:
            return df_cols_lower[name_lower]
    return None

def preprocess_data(df: pd.DataFrame, mapping: dict, config: dict, params: VolcanoParams) -> pd.DataFrame:
    """
    Clean, map, augment, and classify the DataFrame for volcano plot data generation.
    """
    df_processed = df.copy()

    # Get expected column names from config (synonyms)
    expected_pvalue_cols = config.get("expected_columns", {}).get("pvalue_synonyms", ["pvalue", "p_value", "pval", "adj.pval", "fdr"])
    expected_log2fc_cols = config.get("expected_columns", {}).get("log2fc_synonyms", ["log2foldchange", "log2_fc", "logfc", "foldchange"])
    expected_gene_cols = config.get("expected_columns", {}).get("gene_synonyms", ["gene", "gene_symbol", "id", "geneid"])

    # Find actual column names
    pval_col_actual = find_column(df_processed, expected_pvalue_cols, mapping.get("pvalue_col"))
    log2fc_col_actual = find_column(df_processed, expected_log2fc_cols, mapping.get("log2fc_col"))
    gene_col_actual = find_column(df_processed, expected_gene_cols, mapping.get("gene_col"))

    # Validate required columns
    missing_required = []
    if not pval_col_actual: missing_required.append("p-value")
    if not log2fc_col_actual: missing_required.append("log2 fold change")
    if not gene_col_actual: missing_required.append("gene identifier")
    if missing_required:
        raise ValueError(f"Could not find required columns for: {', '.join(missing_required)}. Please map them correctly.")

    # Ensure numeric types
    df_processed[log2fc_col_actual] = pd.to_numeric(df_processed[log2fc_col_actual], errors='coerce')
    df_processed[pval_col_actual] = pd.to_numeric(df_processed[pval_col_actual], errors='coerce')
    df_processed.dropna(subset=[log2fc_col_actual, pval_col_actual], inplace=True)

    # --- FINAL, DATA-ADAPTIVE FIX FOR DATA CUTOFF ---
    # Find the smallest non-zero p-value in the dataset
    non_zero_pvals = df_processed.loc[df_processed[pval_col_actual] > 0, pval_col_actual]
    
    # If there are any non-zero p-values, use them to handle zeros
    if not non_zero_pvals.empty:
        min_pval = non_zero_pvals.min()
        # Replace any p-values of 0 with a value slightly smaller than the minimum
        # to preserve their significance while avoiding log(0) errors.
        df_processed[pval_col_actual] = df_processed[pval_col_actual].replace(0, min_pval * 0.1)
    
    # Compute -log10(p-value) on the cleaned data
    df_processed['_minus_log10_pvalue_'] = -np.log10(df_processed[pval_col_actual])

    # Replace any infinite values that might result from extremely small p-values
    # with a large but finite number, ensuring it's larger than any other point.
    if np.isinf(df_processed['_minus_log10_pvalue_']).any():
        finite_max = df_processed.loc[np.isfinite(df_processed['_minus_log10_pvalue_']), '_minus_log10_pvalue_'].max()
        df_processed.replace([np.inf, -np.inf], finite_max + 10, inplace=True) # Add a fixed amount to ensure it's visibly higher
    # --- END OF FIX ---

    # Classify regulation status
    def classify_regulation(row):
        if row[log2fc_col_actual] >= params.fold_change_threshold and row[pval_col_actual] < params.p_value_threshold:
            return 'up'
        elif row[log2fc_col_actual] <= -params.fold_change_threshold and row[pval_col_actual] < params.p_value_threshold:
            return 'down'
        else:
            return 'neutral'
    df_processed['_classification'] = df_processed.apply(classify_regulation, axis=1)

    # Rename columns to standardized internal names for easier frontend consumption
    df_processed.rename(columns={
        gene_col_actual: '_gene',
        log2fc_col_actual: '_log2fc',
        pval_col_actual: '_pvalue'
    }, inplace=True)

    return df_processed[['_gene', '_log2fc', '_pvalue', '_minus_log10_pvalue_', '_classification']]


# --- REFACTORED Main Entry Point ---

def run(file_obj: Any, params: VolcanoParams, config: dict) -> dict:
    """
    Unified entry point for the volcano tool.
    Processes data and returns a JSON-serializable dictionary for frontend rendering.
    """
    # 1. Determine file extension and get buffer
    file_extension = ""
    if hasattr(file_obj, 'filename') and isinstance(file_obj.filename, str):
        file_extension = os.path.splitext(file_obj.filename)[1].lower()
    
    if not file_extension:
        # Fallback if filename not available. This part might need more robust handling.
        file_extension = ".csv" 

    actual_file_buffer = file_obj.file if hasattr(file_obj, 'file') else file_obj
    actual_file_buffer.seek(0)

    # 2. Load data into DataFrame
    df = load_data(actual_file_buffer, file_extension)

    # 3. Build mapping dict for preprocess_data
    mapping_for_preprocessing = {
        "gene_col": params.gene_col,
        "log2fc_col": params.log2fc_col,
        "pvalue_col": params.pvalue_col
    }
    mapping_for_preprocessing = {k: v for k, v in mapping_for_preprocessing.items() if v is not None}

    # 4. Preprocess and classify data
    df_processed = preprocess_data(df, mapping=mapping_for_preprocessing, config=config, params=params)

    # 5. Prepare summary statistics
    classification_counts = df_processed['_classification'].value_counts().to_dict()
    summary_stats = {
        "total_genes": int(len(df_processed)),
        "initial_upregulated": classification_counts.get('up', 0),
        "initial_downregulated": classification_counts.get('down', 0),
        "initial_neutral": classification_counts.get('neutral', 0),
        "parameters_used": params.model_dump()
    }

    # 6. Prepare default plot configuration from YAML
    # This gives the frontend smart defaults to start with.
    default_plot_config = {
        "title": config.get("graph", {}).get("title", "Volcano Plot"),
        "x_axis_label": "Log2 Fold Change",
        "y_axis_label": "-log10(p-value)",
        "fold_change_threshold": params.fold_change_threshold,
        "p_value_threshold": params.p_value_threshold,
        "colors": config.get("colors", {"up": "#FF0000", "down": "#0000FF", "neutral": "#B0B0B0"}),
        "legend_labels": config.get("legend", {}).get("labels", {})
    }

    # 7. Convert processed dataframe to a list of records for JSON output
    plot_data = df_processed.to_dict(orient='records')

    # 8. Construct the final JSON output
    final_output = {
        "plot_type": "volcano",
        "plot_data": plot_data,
        "summary_stats": summary_stats,
        "default_plot_config": default_plot_config
    }

    return final_output