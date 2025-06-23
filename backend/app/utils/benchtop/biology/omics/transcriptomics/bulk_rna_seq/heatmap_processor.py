# backend/app/utils/benchtop/biology/omics/transcriptomics/bulk_rna_seq/heatmap_processor.py
import pandas as pd
import numpy as np
import io
import os
import re
from typing import Any, Optional, Dict, List

from pydantic import BaseModel, Field
from scipy.cluster.hierarchy import linkage, leaves_list
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# --- Pydantic Schema for Parameters ---
class HeatmapParams(BaseModel):
    analysis_name: Optional[str] = Field("Gene Expression Heatmap", description="Name for the analysis run.")
    gene_selection_method: str = Field("top_n_variable", description="Method to select genes for plotting.")
    top_n_genes: int = Field(50, description="Number of genes for 'top_n_variable' method.")
    de_logfc_threshold: float = Field(1.0, description="LogFC threshold for 'de_genes' method.")
    de_pvalue_threshold: float = Field(0.05, description="P-value/FDR threshold for 'de_genes' method.")
    gene_list: Optional[List[str]] = Field(None, description="A specific list of genes to plot.")
    normalization_method: str = Field("log2_transform", description="How to normalize data before scaling.")
    scaling_method: str = Field("z_score_row", description="How to scale data for visualization.")
    cluster_genes: bool = Field(True, description="Whether to cluster genes (rows).")
    cluster_samples: bool = Field(True, description="Whether to cluster samples (columns).")
    clustering_method: str = Field("average", description="Hierarchical clustering linkage method.")
    distance_metric: str = Field("euclidean", description="Distance metric for clustering.")

    class Config:
        from_attributes = True

# --- Helper Functions ---
def load_data(file_obj: Any, file_extension: str) -> pd.DataFrame:
    try:
        read_func = {'.xlsx': pd.read_excel, '.csv': pd.read_csv, '.tsv': pd.read_csv, '.txt': pd.read_csv}
        kwargs = {'sep': '\t'} if file_extension in ['.tsv', '.txt'] else {}
        return read_func[file_extension](file_obj, **kwargs)
    except KeyError:
        file_obj.seek(0); return pd.read_csv(file_obj)
    except Exception as e:
        raise ValueError(f"Failed to load or parse the data file: {e}")

def infer_groups_from_sample_names(sample_names: List[str]) -> List[str]:
    try:
        prefixes = [re.split(r'[_.-](?:rep|r|s|gfp\w*)?\d*$', name, flags=re.IGNORECASE)[0] for name in sample_names]
        if 1 < len(set(prefixes)) < len(sample_names): return prefixes
        prefixes = [re.split(r'[_.-]', name)[0] for name in sample_names]
        if 1 < len(set(prefixes)) < len(sample_names): return prefixes
    except Exception: pass
    return ['all_samples'] * len(sample_names)

# --- Main Processor Logic ---
def run(file_obj: io.BytesIO, filename: str, params: HeatmapParams, config: dict) -> dict:
    file_extension = os.path.splitext(filename)[1].lower()
    df = load_data(file_obj, file_extension)
    
    df.columns = df.columns.str.strip()
    original_columns_map = {col.lower(): col for col in df.columns}
    df.columns = df.columns.str.lower()

    df = df.set_index(df.columns[0])

    excluded_cols_lower = {str(c).lower() for c in config.get('expected_input', {}).get('excluded_metadata_columns', [])}
    
    sample_columns = [col for col in df.columns if col not in excluded_cols_lower]
    metadata_columns = [col for col in df.columns if col in excluded_cols_lower]
    
    if not sample_columns:
        raise ValueError("No valid sample columns found after excluding metadata.")
    
    expression_matrix = df[sample_columns].apply(pd.to_numeric, errors='coerce')
    gene_metadata = df[metadata_columns]

    imputer = SimpleImputer(strategy='mean')
    expression_matrix = pd.DataFrame(imputer.fit_transform(expression_matrix), 
                                     index=expression_matrix.index, 
                                     columns=expression_matrix.columns)

    selection_reason = ""
    if params.gene_selection_method == "top_n_variable":
        gene_variances = expression_matrix.var(axis=1)
        top_genes = gene_variances.nlargest(params.top_n_genes).index
        matrix_to_plot = expression_matrix.loc[top_genes]
        selection_reason = f"Top {params.top_n_genes} Most Variable Genes"
    elif params.gene_selection_method == "de_genes":
        logfc_col = next((c for c in gene_metadata.columns if 'logfc' in c), None)
        pval_col = next((c for c in gene_metadata.columns if 'pval' in c or 'fdr' in c), None)
        if not logfc_col or not pval_col:
            raise ValueError("For DE gene selection, 'logFC' and 'PValue'/'FDR' columns are required.")
        de_genes = gene_metadata[
            (gene_metadata[logfc_col].abs() >= params.de_logfc_threshold) &
            (gene_metadata[pval_col] < params.de_pvalue_threshold)
        ].index
        matrix_to_plot = expression_matrix.loc[expression_matrix.index.intersection(de_genes)]
        selection_reason = f"Differentially Expressed Genes (|logFC| >= {params.de_logfc_threshold}, p < {params.de_pvalue_threshold})"
    elif params.gene_selection_method == "gene_list" and params.gene_list:
        available_genes = [g for g in params.gene_list if g in expression_matrix.index]
        matrix_to_plot = expression_matrix.loc[available_genes]
        selection_reason = "User-Provided Gene List"
    else:
        raise ValueError("Invalid gene selection method or empty gene list provided.")

    if matrix_to_plot.empty:
        raise ValueError("No genes remained after filtering. Please check your filtering criteria.")

    if params.normalization_method == "log2_transform":
        matrix_to_plot = np.log2(matrix_to_plot + 1)
    
    if params.scaling_method == "z_score_row":
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(matrix_to_plot.T).T
        matrix_to_plot = pd.DataFrame(scaled_data, index=matrix_to_plot.index, columns=matrix_to_plot.columns)

    gene_order, sample_order = matrix_to_plot.index.tolist(), matrix_to_plot.columns.tolist()

    if params.cluster_genes:
        linkage_matrix_genes = linkage(matrix_to_plot, method=params.clustering_method, metric=params.distance_metric)
        gene_order = matrix_to_plot.index[leaves_list(linkage_matrix_genes)].tolist()

    if params.cluster_samples:
        linkage_matrix_samples = linkage(matrix_to_plot.T, method=params.clustering_method, metric=params.distance_metric)
        sample_order = matrix_to_plot.columns[leaves_list(linkage_matrix_samples)].tolist()
    
    final_matrix = matrix_to_plot.loc[gene_order, sample_order]
    final_sample_names = [original_columns_map[col] for col in final_matrix.columns]
    
    plot_data = {
        "heatmap_values": final_matrix.values.tolist(),
        "gene_labels": final_matrix.index.tolist(),
        "sample_labels": final_sample_names,
        "sample_annotations": infer_groups_from_sample_names(final_sample_names)
    }

    summary_stats = {
        "genes_plotted": len(final_matrix.index),
        "samples_plotted": len(final_matrix.columns),
        "gene_selection_reason": selection_reason,
        "parameters_used": params.model_dump()
    }
    
    plot_config_from_yaml = config.get("default_plot_config", {})
    default_plot_config = {
        "title": params.analysis_name, "subtitle": selection_reason,
        "color_map": plot_config_from_yaml.get("color_map", "RdBu_r"),
        "show_gene_labels": plot_config_from_yaml.get("show_gene_labels", True),
        "show_sample_labels": plot_config_from_yaml.get("show_sample_labels", True),
        "show_sample_annotation": plot_config_from_yaml.get("show_sample_annotation", True),
        "hover_template": plot_config_from_yaml.get("hover_template", "Value: %{z:.2f}")
    }
    return {
        "plot_type": "heatmap", "plot_data": plot_data,
        "summary_stats": summary_stats, "default_plot_config": default_plot_config
    }