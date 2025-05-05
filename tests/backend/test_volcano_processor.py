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

def test_load_data(sample_df):
    """
    Verify that load_data returns a DataFrame with the sample's raw columns.
    """
    assert not sample_df.empty, "Sample DataFrame should not be empty"
    for col in ["Gene", "logFC", "PValue"]:
        assert col in sample_df.columns, f"Expected column {col} in DataFrame"

def test_preprocess_and_plot(sample_df):
    """
    Run preprocessing with explicit column mappings, then plot.
    """
    # In production your API will accept these names from the user
    df_processed = preprocess_data(
        sample_df,
        pvalue_col="PValue",
        log2fc_col="logFC",
        gene_col="Gene"
    )

    # Check that a derived score or similar column appears
    score_cols = [c for c in df_processed.columns if "score" in c.lower()]
    assert score_cols, "Preprocessed DataFrame should contain a 'score' column"

    # Generate a volcano plot with user-specified axes
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

    # Convert to base64 and assert a valid data URI
    b64 = fig_to_base64(fig)
    assert isinstance(b64, str) and b64.startswith("data:image/png;base64,"), "Expected a base64 PNG data URI"
