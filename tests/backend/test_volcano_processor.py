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
    Without specifying column names, preprocess_data should
    locate columns using its built-in synonyms and produce
    a composite_score column.
    """
    df_processed = preprocess_data(sample_df)
    assert "composite_score" in df_processed.columns

def test_explicit_mapping_works(sample_df):
    """
    When the user provides their own column names mapping,
    preprocess_data must honor them.
    """
    mapping = {"pvalue": "PValue", "log2fc": "logFC", "gene": "Gene"}
    df_processed = preprocess_data(sample_df, mapping=mapping)
    assert "composite_score" in df_processed.columns

def test_plot_and_base64(sample_df):
    """
    Generate a volcano plot using explicit column names,
    then convert to a base64 data URI.
    """
    mapping = {"pvalue": "PValue", "log2fc": "logFC", "gene": "Gene"}
    df_processed = preprocess_data(sample_df, mapping=mapping)

    fig = plot_volcano(
        df=df_processed,
        label_genes=[],
        title="Test Volcano",
        xlabel="Log2 Fold Change",
        ylabel="-Log10 P-Value",
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
    # Must be a string and include the data URI prefix
    assert isinstance(b64, str)
    assert b64.startswith("data:image/png;base64,")
