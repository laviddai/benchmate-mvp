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
    """
    Return the first matching column name from expected_names in df.columns.
    """
    for name in expected_names:
        if name in df.columns:
            return name
    return None


def preprocess_data(df, mapping=None):
    """
    Clean, map, and augment the DataFrame for downstream plotting.
    - Lowercases column names
    - Applies user-supplied mapping of fields to columns
    - Computes -log10(p-value) and composite_score
    """
    # Normalize headers
    df.columns = df.columns.str.strip().str.lower()

    # Default synonyms
    synonyms = {
        "pvalue": ["pvalue", "p_value", "pval"],
        "log2fc": ["log2foldchange", "log2_fc", "logfc", "foldchange"],
        "gene": ["gene", "gene_symbol"]
    }

    # Apply user mapping overrides
    if mapping:
        mapping_norm = {k.lower(): v.strip().lower() for k, v in mapping.items()}
        for key, col in mapping_norm.items():
            synonyms[key] = [col] + synonyms.get(key, [])

    # Locate actual columns
    pval_col = find_column(df, synonyms["pvalue"])
    fc_col   = find_column(df, synonyms["log2fc"])
    gene_col = find_column(df, synonyms["gene"])

    missing = [f for f, c in zip(["pvalue","log2fc","gene"], [pval_col,fc_col,gene_col]) if c is None]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}. Available: {df.columns.tolist()}")

    # Compute -log10(p-value)
    df["-log10_y"] = -np.log10(df[pval_col])
    # Use calculated_log2fc if present, else detected fold change
    fc_vals = df.get("calculated_log2fc", df[fc_col])
    # Composite score
    df["composite_score"] = np.abs(fc_vals) * (-np.log10(df[pval_col]))

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
    Generate a volcano plot with classification and optional gene labels.
    Returns a Matplotlib Figure.
    """
    df = df.copy()
    # Case-insensitive lookup
    df.columns = df.columns.str.strip().str.lower()
    x = x_col.strip().lower()
    y = y_col.strip().lower()
    g = gene_col.strip().lower()

    # Classify regulation
    df["regulation"] = "neutral"
    df.loc[(df[x] >= fc_thresh) & (df[y] <= pval_thresh), "regulation"] = "up"
    df.loc[(df[x] <= -fc_thresh) & (df[y] <= pval_thresh), "regulation"] = "down"
    df["-log10_y"] = -np.log10(df[y])

    fig, ax = plt.subplots(figsize=figsize)
    for grp in df["regulation"].unique():
        grp_df = df[df["regulation"] == grp]
        ax.scatter(grp_df[x], grp_df["-log10_y"], label=legend_labels.get(grp),
                   color=colors.get(grp), alpha=0.7)
    if label_genes:
        for _, row in df[df[g].isin(label_genes)].iterrows():
            ax.text(row[x], row["-log10_y"], row[g], fontsize=8, alpha=0.8)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.grid(show_grid)
    if log_scale_y:
        ax.set_yscale("log")
    if legend_position == "outside right":
        ax.legend(title=legend_title, loc="center left", bbox_to_anchor=(1,0.5))
    else:
        ax.legend(title=legend_title, loc=legend_position)
    if show_threshold_line:
        ax.axhline(y=-np.log10(pval_thresh), linestyle="--", color="black", linewidth=1)
    if footer_text:
        ax.text(0.5, -0.15, footer_text, transform=ax.transAxes,
                ha="center", va="top", fontsize=8, color="gray")
    return fig


def fig_to_base64(fig):
    """
    Convert a Matplotlib figure to a data URI with base64-encoded PNG.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img_bytes = buf.read()
    base64_str = base64.b64encode(img_bytes).decode("utf-8")
    # Prepend data URI header
    return f"data:image/png;base64,{base64_str}"
