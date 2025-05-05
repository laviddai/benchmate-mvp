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
    # Locate the bundled sample data file
    here = os.path.dirname(__file__)
    sample_path = os.path.abspath(os.path.join(here, os.pardir, "data", "sample_bulk_rna.xlsx"))
    with open(sample_path, "rb") as f:
        df = load_data(f, ".xlsx")
    return df

def test_load_data(sample_df):
    # Ensure the DataFrame loaded has rows and expected columns
    assert not sample_df.empty
    for col in ["gene", "fold_change", "p_value"]:
        assert col in sample_df.columns

def test_preprocess_and_plot(sample_df):
    # Map your sample’s headers to the processor’s defaults
    df_processed = preprocess_data(
        sample_df,
        mapping={"pvalue": "p_value", "log2fc": "fold_change"}
    )
    # After preprocessing you should have the composite score column
    assert "composite_score" in df_processed.columns

    # Generate a volcano plot
    fig = plot_volcano(
        df=df_processed,
        label_genes=[],
        title="Test Volcano",
        xlabel="Log2 Fold Change",
        ylabel="-Log10(P-value)",
        x_col="log2foldchange",
        y_col="p_value",
        gene_col="gene",
        fc_thresh=1.0,
        pval_thresh=0.05,
        legend_title="Regulation",
        show_threshold_line=True,
        footer_text="Footer"
    )
    # Convert to base64 and assert we got a string back
    b64 = fig_to_base64(fig)
    assert isinstance(b64, str) and b64.startswith("data:image/png;base64,")
