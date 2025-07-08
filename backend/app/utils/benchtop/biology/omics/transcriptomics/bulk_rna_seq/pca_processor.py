import pandas as pd
import numpy as np
import io
import os
import re
import logging
from typing import Any, Optional, Dict, List

from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA

from app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.pca_schema import PCAParams

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def load_data(file_obj: Any, file_extension: str) -> pd.DataFrame:
    try:
        read_func = {
            '.xlsx': pd.read_excel,
            '.csv': pd.read_csv,
            '.tsv': pd.read_csv,
            '.txt': pd.read_csv,
        }
        kwargs = {'sep': '\t'} if file_extension in ['.tsv', '.txt'] else {}
        return read_func[file_extension](file_obj, **kwargs)
    except KeyError:
        logger.warning("Unknown extension '%s', trying generic CSV read.", file_extension)
        file_obj.seek(0)
        return pd.read_csv(file_obj)
    except Exception as e:
        raise ValueError(f"Failed to load or parse the data file: {e}")


def infer_groups_from_sample_names(sample_names: List[str]) -> List[str]:
    try:
        prefixes = [re.split(r'[_.-](?:rep|r|s|gfp\w*)?\d*$', name, flags=re.IGNORECASE)[0]
                    for name in sample_names]
        if 1 < len(set(prefixes)) < len(sample_names):
            return prefixes
        prefixes = [re.split(r'[_.-]', name)[0] for name in sample_names]
        if 1 < len(set(prefixes)) < len(sample_names):
            return prefixes
    except Exception:
        pass
    return ['all_samples'] * len(sample_names)

# --- Main Processor Logic ---
def run(file_obj: io.BytesIO, filename: str, params: PCAParams, config: dict) -> dict:
    file_extension = os.path.splitext(filename)[1].lower()
    df = load_data(file_obj, file_extension)

    # Trim whitespace from column headers
    df.columns = df.columns.str.strip()
    logger.info("Columns after trimming: %r", df.columns.tolist())

    # 1. Set Gene Index
    df = df.set_index(df.columns[0])
    logger.info("DataFrame shape after indexing gene names: %s", df.shape)

    # 2. Identify metadata columns to exclude (from config and grouping)
    metadata_cols = config.get('expected_input', {}).get('excluded_metadata_columns', []) or []
    if params.grouping_column:
        metadata_cols.append(params.grouping_column)
    metadata_cols_lower = {str(col).strip().lower() for col in metadata_cols}
    logger.info("Excluding metadata columns: %s", metadata_cols_lower)

    # 3. Select sample columns by excluding metadata columns
    final_sample_columns = [col for col in df.columns
                             if col.strip().lower() not in metadata_cols_lower]
    if not final_sample_columns:
        raise ValueError("No valid sample columns found after excluding metadata. "
                         "Check your data file and configuration.")
    logger.info("Final sample columns selected: %r", final_sample_columns)

    df_samples_only = df[final_sample_columns]

    # 4. Convert to numeric and transpose
    df_numeric = df_samples_only.apply(pd.to_numeric, errors='coerce')
    data_for_pca = df_numeric.T  # Transpose: (samples x genes)
    logger.info("Shape of data_for_pca (samples x genes): %s", data_for_pca.shape)

    # 5. Impute missing values and scale if requested
    imputer = SimpleImputer(strategy='mean')
    data_imputed = imputer.fit_transform(data_for_pca)
    data_scaled = StandardScaler().fit_transform(data_imputed) if params.scale_data else data_imputed

    n_samples, n_features = data_scaled.shape
    if n_samples < 2 or n_features < 2:
        raise ValueError(f"PCA requires at least 2 samples and 2 features. Found {n_samples} samples and {n_features} features.")

    # 6. Run PCA
    n_components = min(params.n_components, n_samples, n_features)
    pca = PCA(n_components=n_components)
    principal_components = pca.fit_transform(data_scaled)
    explained_variance = pca.explained_variance_ratio_
    logger.info("Explained variance ratios: %s", explained_variance)

    # 7. Prepare results
    pc_columns = [f"PC{i+1}" for i in range(n_components)]
    results_df = pd.DataFrame(principal_components, columns=pc_columns, index=data_for_pca.index)
    results_df = results_df.rename_axis('sample').reset_index()
    results_df['group'] = infer_groups_from_sample_names(results_df['sample'].tolist())

    # 8. Build output
    pc_x_idx, pc_y_idx = params.pc_x_axis - 1, params.pc_y_axis - 1
    if not (0 <= pc_x_idx < n_components and 0 <= pc_y_idx < n_components):
        raise ValueError(f"Requested PCs are out of bounds for the {n_components} components calculated.")

    return {
        "plot_type": "pca",
        "plot_data": results_df.to_dict(orient='records'),
        "summary_stats": {
            "total_samples": n_samples,
            "total_genes": n_features,
            "explained_variance_ratio": explained_variance.tolist(),
            "parameters_used": params.model_dump()
        },
        "default_plot_config": {
            "title": params.analysis_name,
            "pc_x_axis": params.pc_x_axis,
            "pc_y_axis": params.pc_y_axis,
            "x_axis_label": f"PC{params.pc_x_axis} ({explained_variance[pc_x_idx]:.1%})",
            "y_axis_label": f"PC{params.pc_y_axis} ({explained_variance[pc_y_idx]:.1%})",
            "point_size": config.get("default_plot_config", {}).get("point_size", 8),
        }
    }
