# tests/backend/test_volcano_processor.py

import os
import pandas as pd
import pytest

from backend.app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano_processor import (
    load_data,
    preprocess_data,
    plot_volcano,
    fig_to_base64,
)

@pytest.fixture
def sample_df():
    """
    Load the bundled sample Excel file into a DataFrame.
    """
    here = os.path.dirname(__file__)
    sample_path = os.path.abspath(os.path.join(here, os.pardir, "data", "sample_bulk_rna.xlsx"))
    with open(sample_path, "rb") as f:
        df = load_data(f, ".xlsx")
    return df

def test_default_mapping_works(sample_df):
    """
    With no mapping, preprocess_data should still locate columns
    named like 'gene', 'p_value', 'log2foldchange', etc.
    """
    # This assumes your sample data has at least one of the synonyms
    # defined in preprocess_data's defaults (e.g. 'PValue', 'logFC', 'Gene').
    df_processed = preprocess_data(sample_df)
    # It must compute the composite score
    assert "composite_score" in df_processed.columns

def test_explicit_mapping_works(sample_df):
    """
    Override the default synonyms via the mapping argument;
    verify that preprocess_data picks up the exact names you give.
    """
    # Suppose our sample has headers "PValue", "logFC", "Gene"
    mapping = {
        "pvalue": "PValue",
        "log2fc": "logFC",
        "gene": "Gene"
    }
    df_processed = preprocess_data(sample_df, mapping=mapping)

    # After mapping, composite_score must still be present
    assert "composite_score" in df_processed.columns

def test_plot_and_base64(sample_df):
    """
    Finally, generate a plot with explicit mapping and
    check that the base64-encoded PNG URI is returned.
    """
    mapping = {
        "pvalue": "PValue",
        "log2fc": "logFC",
        "gene": "Gene"
    }
    df_processed = preprocess_data(sample_df, mapping=mapping)

    fig = plot_volcano(
        df=df_processed,
        label_genes=[],
        title="Test Volcano",
        xlabel="Log2 Fold Change",
        ylabel="-Log10 P-Value",
        # Notice: plot_volcano takes the **actual** column names here,
        # since you’ve already told preprocess_data which they are.
        x_col="logFC",
        y_col="PValue",
        gene_col="Gene",
        fc_thresh=1.0,
        pval_thresh=0.05,
        legend_title="Regulation",
        show_threshold_line=True,
        footer_text="Footer"
    )

    b64 = fig_to_base64(fig)
    assert isinstance(b64, str) and b64.startswith("data:image/png;base64,")
