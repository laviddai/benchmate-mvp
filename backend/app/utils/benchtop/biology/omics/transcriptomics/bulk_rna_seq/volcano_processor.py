# backend/app/utils/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano-processor.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

def load_data(file_obj, ext):
    """
    Load data from a file object based on its extension.
    Parameters:
      file_obj: A file-like object.
      ext: The file extension (e.g., ".csv", ".xlsx").
    Returns:
      A pandas DataFrame.
    """
    if ext in ['.xls', '.xlsx']:
        return pd.read_excel(file_obj)
    else:
        return pd.read_csv(file_obj)

def find_column(df, expected_names):
    for name in expected_names:
        if name in df.columns:
            return name
    return None

def preprocess_data(df, mapping=None):
    # Clean column headers: lower-case and strip whitespace
    df.columns = df.columns.str.strip().str.lower()

    # Define default synonyms
    synonyms = {
        "pvalue": ["pvalue", "p_value", "pval"],
        "log2fc": ["log2foldchange", "log2_fc", "logfc", "foldchange"],
        "gene": ["gene", "gene_symbol"]
    }

    # If a user-supplied mapping is provided, update the synonyms for those keys.
    if mapping:
        # Normalize the keys and values from the mapping.
        mapping_normalized = {k.lower(): v.strip().lower() for k, v in mapping.items()}
        for key in mapping_normalized:
            # Override the synonyms with the user provided value as the top priority.
            synonyms[key] = [mapping_normalized[key]] + synonyms.get(key, [])
    
    # Find the actual column in the DataFrame for each required field.
    pval_col = find_column(df, synonyms["pvalue"])
    fc_col = find_column(df, synonyms["log2fc"])
    gene_col = find_column(df, synonyms["gene"])

    missing = [field for field, col in zip(["pvalue", "log2fc", "gene"], [pval_col, fc_col, gene_col]) if col is None]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}. Available columns: {df.columns.tolist()}")

    # Compute -log10 of the p-value column.
    df["-log10_y"] = -np.log10(df[pval_col])
    
    # Use 'calculated_log2fc' if available; if not, use the found fold change column.
    if "calculated_log2fc" in df.columns:
        fc_values = df["calculated_log2fc"]
    else:
        fc_values = df[fc_col]
    
    # Compute composite score.
    df["composite_score"] = np.abs(fc_values) * (-np.log10(df[pval_col]))
    
    return df

def plot_volcano(
    df,
    label_genes=None,
    title="Volcano Plot",
    xlabel="log2 Fold Change",
    ylabel="-log10(p-value)",
    x_col="log2FoldChange",
    y_col="pvalue",
    gene_col="gene",
    fc_thresh=1.0,
    pval_thresh=0.05,
    legend_title="Regulation",
    colors={"up": "red", "down": "blue", "neutral": "gray"},
    legend_labels={"up": "Up", "down": "Down", "neutral": "Neutral"},
    show_grid=True,
    legend_position="best",
    figsize=(8, 6),
    xlim=(-5, 5),
    ylim=(0, 10),
    log_scale_y=False,
    show_threshold_line=False,
    footer_text=None
):
    """
    Generate a volcano plot from the given DataFrame.
    Parameters:
      df: The processed DataFrame.
      label_genes: List of gene names to highlight (optional).
      title, xlabel, ylabel: Plot title and axis labels.
      x_col, y_col, gene_col: Column names for fold change, p-value, and gene names.
      fc_thresh: Threshold on the x-axis to classify regulation.
      pval_thresh: p-value threshold for significance.
      legend_title, colors, legend_labels: Legend configuration.
      show_grid, legend_position, figsize, xlim, ylim, log_scale_y, show_threshold_line: Plot appearance options.
      footer_text: Optional footer text to annotate the figure.
    Returns:
      A Matplotlib figure object.
    """
    # Prepare a copy to avoid modifying the original DataFrame
    df = df.copy()
    # Classify regulation states
    df["regulation"] = "neutral"
    df.loc[(df[x_col] >= fc_thresh) & (df[y_col] <= pval_thresh), "regulation"] = "up"
    df.loc[(df[x_col] <= -fc_thresh) & (df[y_col] <= pval_thresh), "regulation"] = "down"
    df["-log10_y"] = -np.log10(df[y_col])
    
    # Create plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot each regulation group
    for group in df["regulation"].unique():
        group_data = df[df["regulation"] == group]
        ax.scatter(group_data[x_col], group_data["-log10_y"],
                   label=legend_labels.get(group, group),
                   color=colors.get(group, "gray"),
                   alpha=0.7)
    
    # Optionally label selected genes
    if label_genes:
        for _, row in df[df[gene_col].isin(label_genes)].iterrows():
            ax.text(row[x_col], row["-log10_y"], row[gene_col],
                    fontsize=8, alpha=0.8)
    
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.grid(show_grid)
    
    if log_scale_y:
        ax.set_yscale("log")
    
    # Place legend
    if legend_position == "outside right":
        ax.legend(title=legend_title, loc="center left", bbox_to_anchor=(1, 0.5))
    else:
        ax.legend(title=legend_title, loc=legend_position)
        
    if show_threshold_line:
        threshold_line = -np.log10(pval_thresh)
        ax.axhline(y=threshold_line, linestyle="--", color="black", linewidth=1)
    
    if footer_text:
        ax.text(0.5, -0.15, footer_text, transform=ax.transAxes,
                ha="center", va="top", fontsize=8, color="gray")
    
    return fig

def fig_to_base64(fig):
    """
    Convert a Matplotlib figure to a base64-encoded PNG string.
    Parameters:
      fig: A Matplotlib figure.
    Returns:
      A base64-encoded string representing the figure image.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_bytes = buf.read()
    base64_str = base64.b64encode(img_bytes).decode("utf-8")
    return base64_str
