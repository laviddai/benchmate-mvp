**Prompt for Backend Analysis Module Implementation (Example: New PCA Plot Tool):**

"Hello! We're expanding the BenchTop analytical workbench within the BenchMate project. I need to design and implement a new **backend analysis module for generating PCA plots from bulk RNA-seq data**.

**Key Contextual Documents (assume accessible):**
*   **Product Requirements for new tools:** `docs/prd.md` (Version 0.3)
    *   *Focus on:* Section 3.2 (Bulk RNA-Seq Module scope, including PCA), Section 2.2 (Guiding Principles - especially scientific rigor, publication-quality output, parameterization).
*   **Architectural Pattern for Analysis Modules:** `docs/architecture.md` (Version 0.2)
    *   *Focus on:* Section 3.3 (Async Task Processing), Section 3.5 (Configuration System), and how `backend/app/utils/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano_processor.py` and `backend/app/config/benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.yaml` serve as templates.
*   **Overall Project Stack & Guidelines:** Refer to my system instructions for your persona, preferred technologies (Python, FastAPI, Celery, Pandas, Matplotlib/Seaborn), and coding standards.

The new PCA plot module should:
1.  Have a corresponding YAML configuration file defining its parameters (e.g., columns for sample grouping, number of principal components).
2.  Include a Python processor script (similar to `volcano_processor.py`) that:
    *   Takes a dataset (e.g., gene expression matrix from S3).
    *   Performs PCA using appropriate libraries (e.g., scikit-learn).
    *   Generates a PCA plot (using Matplotlib/Seaborn) showing samples colored by group, with explained variance.
    *   Returns the plot image and any relevant summary statistics (e.g., explained variance per component).
3.  Be integrated into a new Celery task.
4.  Have a new FastAPI endpoint for job submission (e.g., `/api/analyses/pca-plot/submit`).

Please confirm you have this context. Our first step will be to define the YAML configuration structure for the PCA plot tool."