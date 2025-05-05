# tests/backend/test_volcano_processor.py

import os
from backend.app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano_processor import (
    load_data,
    preprocess_data,
    plot_volcano,
    fig_to_base64,
)
import pandas as pd

# Path to your sample Excel file (update the path if necessary)
sample_file = r"C:\Users\Lenovo\Desktop\BenchMate Files\CAGRF221112648-Mutant.Gut.GFPpos_v_Control.Gut.GFPpos-all_genes.xlsx"
ext = ".xlsx"

# Load the file
with open(sample_file, "rb") as f:
    df = load_data(f, ext)

# Optional: print the columns after cleaning to debug the mapping
df.columns = df.columns.str.strip().str.lower()
print("Detected columns:", df.columns.tolist())

# Define expected column names based on your file.
# For example, if your file headers are "gene", "fold_change", "p_value" (after cleaning, they become "gene", "fold_change", "p_value")
# And your defaults expect "gene", "log2foldchange", and "pvalue", then specify a mapping.
mapping = {
    "log2fc": "fold_change",  # if your fold-change column is named 'fold_change'
    "pvalue": "p_value"       # if your p-value column is named 'p_value'
}

# Preprocess the data with the mapping (if needed)
try:
    df_processed = preprocess_data(df, mapping=mapping)
    print("Preprocessing successful. New columns added:", ["-log10_y", "composite_score"])
except Exception as e:
    print("Error in preprocessing:", e)

# Now generate the volcano plot.
# Adjust parameters (like thresholds) according to your sample data.
try:
    fig = plot_volcano(
        df=df_processed,
        label_genes=[],  # You may set a list of genes to label as needed.
        title="Test Volcano Plot",
        xlabel="Log2 Fold Change",
        ylabel="-Log10(P-value)",
        x_col="log2foldchange",  # this should match the key in your mapping or defaults
        y_col="p_value",         # should match, considering our mapping
        gene_col="gene",
        fc_thresh=1.0,
        pval_thresh=0.05,
        legend_title="Regulation",
        show_threshold_line=True,
        footer_text="Test Footer"
    )
    # Convert the plot to a base64 string.
    b64_str = fig_to_base64(fig)
    print("Plot successfully generated and converted to base64:")
    print(b64_str[:200])  # Print the first 200 characters for inspection
except Exception as e:
    print("Error generating plot:", e)
