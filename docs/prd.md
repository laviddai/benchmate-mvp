# Product Requirements Document: BenchMate & BenchTop

**Version:** 0.3
**Date:** June 7, 2025
**Status:** Approved for MVP Development Phase

## 1. Introduction & Vision

### 1.1. Purpose of this Document
This document outlines the product requirements for BenchMate, a platform designed to unify scientific research workflows, data analysis, visualization, and collaboration. It will detail the vision, features, user stories, and technical considerations, with an initial focus on the Minimum Viable Product (MVP) for **BenchTop**, the core analytical workbench.

### 1.2. Overall Vision
*   Unify social collaboration (**BenchMate** - social/community platform) and advanced research tools (**BenchTop** - analytical workbench) under one coherent experience.
*   Lower the activation energy for data analysis & visualization across various scientific domains, while preserving scientific rigor and aiming for publication-ready outputs.
*   Empower scientists by making complex computational tools accessible through an intuitive, user-friendly interface.
*   Verify researcher identity (e.g., via ORCID), yet keep space for the broader public to learn and ask questions (primarily via the BenchMate social platform).

### 1.3. Problem Statement
Scientific research today is often fragmented. Researchers juggle a patchwork of single-purpose tools, face steep learning curves for computational methods, and find interdisciplinary collaboration challenging. Communicating findings, even within labs, can be inefficient, and public access to scientific knowledge is limited. BenchMate aims to address these pain points.

### 1.4. Target Audience
*   **Primary (BenchTop - Broader Scope):**
    *   Researchers across various **biological science domains** (e.g., molecular biology, cell biology, neuroscience, immunology) who work with diverse data types including omics (transcriptomics, proteomics), imaging, electrophysiology, etc.
    *   The MVP will *initially demonstrate capability* with bulk RNA-seq analysis and aim to include foundational ImageJ/Fiji-like image processing functionalities, serving as a template for expansion into other biological areas.
*   **Secondary (Broader BenchMate Vision & Future Expansion):**
    *   Researchers in other scientific disciplines (e.g., chemistry, physics) as the platform's configurable nature allows.
    *   Medical professionals in translational research.
    *   Core facilities & CROs needing reproducible analysis pipelines.
    *   Educators and students in STEM fields.
    *   Science-curious public & students (for the BenchMate social platform).

### 1.5. Goals & Success Metrics (High-Level)
*   **Goal (BenchTop MVP):**
    *   Deliver a functional and reliable platform for users to upload data (starting with bulk RNA-seq data as the first implemented technique).
    *   Successfully perform key analyses for the initial technique(s) (e.g., Volcano Plots, PCA, Heatmaps for bulk RNA-seq).
    *   Provide foundational capabilities for an ImageJ/Fiji-like image processing workbench, allowing image manipulation, data collection, and subsequent analysis/visualization.
    *   Enable users to visualize results interactively, make final adjustments to plots (e.g., legends, titles, statistical annotations), and export publication-quality figures and data.
    *   Establish a flexible framework that clearly demonstrates the pathway to incorporating a wide array of other biological tools and techniques.
*   **Success Metrics (BenchTop MVP - Qualitative initially):**
    *   Successful end-to-end completion of implemented analysis workflows (e.g., bulk RNA-seq, basic image processing pipeline) by test users.
    *   Positive feedback on the usability of the parameter input, interactive plot adjustments, and result interpretation across different experimental setups.
    *   Ability for users to generate figures that require minimal external editing for reports/publications.
    *   Stable and reliable performance of the backend asynchronous processing.
    *   Clear understanding by test users of how BenchTop can be extended to other data types and analyses.

## 2. Platform Overview

### 2.1. Platform Split & Integration
*   **BenchMate (Social Side):**
    *   **Purpose:** Community hub for sharing findings, asking/answering questions, and networking.
    *   **Development:** Being developed in parallel by another team member.
    *   **Planned Backend:** Supabase.
    *   **Integration Plan:** Will be integrated with BenchTop to allow seamless sharing of analyses and results, and to leverage shared user authentication.
*   **BenchTop (Tool Side - Current MVP Focus):**
    *   **Purpose:** Interactive workbench for uploading diverse scientific data, running a wide array of analyses, and generating customizable, publication-quality visualizations.
    *   **Frontend:** Next.js (React) - `frontend/benchtop-nextjs/`.
    *   **Backend:** Python micro-services (FastAPI, Celery workers), YAML-driven tool configs, PostgreSQL (metadata), MinIO (file storage).
    *   **Authentication (MVP):** Utilize backend placeholder; (Future: Integrate with BenchMate’s Supabase Auth with mandatory ORCID verification for access).

### 2.2. Guiding Principles for BenchTop
*   **Scientifically Rigorous:** Analyses should follow best practices for each domain.
*   **User-Friendly & Accessible:** Intuitive UI/UX, minimizing the need for coding expertise.
*   **Publication-Quality Outputs with User Refinement:** Figures and tables should be high quality by default, with robust options for users to make final adjustments (legends, titles, colors, statistical annotations).
*   **Comprehensive Parameterization:** Allow users to specify parameters that accurately reflect diverse experimental designs across many techniques.
*   **Reproducibility:** Track provenance and enable users to replay or share analysis pipelines.
*   **Modularity & Extensibility:** Design for easy addition of new tools, techniques, and scientific domains.
*   **Security & User Control:** Prioritize data security, user privacy, and user control over their data.

## 3. BenchTop MVP: Demonstrating a Generalizable Workflow

### 3.1. Core User Workflow (Applicable Across Techniques)
The following workflow, while initially implemented and tested with **bulk RNA-seq data** and **foundational imaging tasks**, is designed to be a **generalizable template** for incorporating numerous other scientific techniques and tools into BenchTop. The goal is to make researchers' lives easier by providing a consistent and intuitive process for various data types.

*   **User Story (Example - Generalizable):** As a scientist, I want to upload my experimental data (e.g., omics tables, imaging files, electrophysiology traces), select an appropriate analysis or visualization tool from a comprehensive list relevant to my data type, easily input my specific experimental parameters and conditions, run the analysis efficiently, view interactive and high-quality results. I then want to be able to **add final touches to these visualizations (e.g., adjust legends, titles, add statistical significance markers, modify lines/points) and extract key information (e.g., lists of significant genes, quantitative image measurements)** before exporting these refined results (plots, processed data) for my reports, publications, or further investigation.

### 3.2. Initial Implementations for MVP
*   **Bulk RNA-Seq Module (First Detailed Implementation):**
    *   **Analyses:** Volcano Plot, PCA Plot, Heatmap, Differential Expression Table.
    *   This module will serve as the primary example of how new techniques are integrated.
*   **ImageJ/Fiji-like Workbench (Foundational Steps):**
    *   Begin development of core functionalities for an integrated image processing environment.
    *   **MVP Goal:** Users should be able to upload images, perform basic manipulations (e.g., brightness/contrast, cropping, perhaps a simple filter), collect quantitative data from images based on user-defined parameters or simple ROIs (e.g., area, intensity counts), organize this extracted data, and then directly use this data for subsequent basic data analysis and visualizations within BenchTop (e.g., generating dot plots, scatter plots, or bar charts from the quantified image data). This demonstrates the seamless flow from image to data to plot.

### 3.3. Functional Requirements (Barebones Frontend for BenchTop MVP - Generalizable)

#### 3.3.1. Project Context & Data Management
*   **F-REQ-001:** Users must be able to select an existing project to work within.
*   **F-REQ-002 (Data Upload):**
    *   Provide an interface to upload various data files (initial focus: CSV/TSV/XLSX for bulk RNA-seq; design to accommodate other types like .CZI/TIFFs for imaging later).
    *   User selects the project ID for the dataset.
    *   The system shall use the `POST /api/datasets/upload-and-create/` endpoint.
    *   Display feedback on upload success/failure.
    *   The system should ideally attempt to auto-detect data type or allow user specification to guide tool suggestions.
*   **F-REQ-003 (Dataset Selection):** Allow users to select a previously uploaded dataset within the current project for analysis.

#### 3.3.2. Analysis Configuration & Execution
*   **F-REQ-004 (Analysis/Tool Selection):**
    *   After data upload/selection, allow the user to choose a specific analysis/visualization tool from a list relevant to the (detected/specified) data type or scientific technique.
*   **F-REQ-005 (Parameter Input):**
    *   Dynamically display input fields relevant to the selected tool and technique.
    *   **Example for any tool:** Input fields should be clearly labeled, with tooltips explaining each parameter. The UI must be designed to be intuitive, allowing users to easily map their diverse experimental designs and stipulations to these parameters.
    *   **Bulk RNA-Seq Volcano Plot Example:** Gene Column, Log2FC Column, P-value Column, Thresholds, Analysis Name.
*   **F-REQ-006 (Job Submission):**
    *   A "Run Analysis" button to submit the job to the backend.
    *   Call the appropriate tool submission endpoint (e.g., `POST /api/analyses/{tool_name}/submit`).
    *   Store the returned `analysis_run_id`.
    *   Provide immediate feedback.

#### 3.3.3. Job Monitoring & Results Display/Interaction
*   **F-REQ-007 (Status Polling & Display):**
    *   Periodically poll `GET /api/analysis-runs/{analysis_run_id}`.
    *   Display current job status.
    *   If `FAILED`, display the error message.
*   **F-REQ-008 (Results Display & Interaction):**
    *   When status is `COMPLETED`:
        *   Retrieve `output_artifacts` (e.g., `plot_image_s3_path`, `summary_stats`, underlying processed data tables).
        *   Fetch presigned URL(s) for output files.
        *   Render plots with intelligent defaults (e.g., automatic axis scaling based on uploaded data).
        *   Provide interactive controls for users to **refine the visualization post-generation**:
            *   Adjust legends (visibility, position, labels).
            *   Modify titles and axis labels.
            *   Add/edit statistical significance annotations (e.g., p-value stars/bars).
            *   Customize colors, point shapes/sizes, line styles (where applicable).
        *   Allow users to **extract specific information from the visualization or underlying data**.
            *   **Example (Volcano Plot):** Provide a way to view or export lists of significantly upregulated or downregulated genes based on current thresholds.
            *   **Example (Image Analysis):** Display tables of quantified measurements.
        *   Display any summary statistics or links to downloadable data tables.
*   **F-REQ-009 (Result Export):**
    *   Allow users to download the *refined* plot image (PNG, SVG, PDF).
    *   Allow download of processed data tables (e.g., differential expression list, quantified image data).

### 3.4. Non-Functional Requirements (BenchTop MVP)
*   **NF-REQ-001 (Usability - Functional Focus):** Primary goal is functionality and demonstrating the generalizable end-to-end workflow. UI will be barebones, using existing shadcn/ui components functionally without extensive custom styling.
*   **NF-REQ-002 (Performance - Backend):** Backend analysis tasks should complete within a reasonable timeframe for typical datasets of the implemented techniques.
*   **NF-REQ-003 (Reliability):** The analysis pipeline should be robust, with clear error handling and reporting.
*   **NF-REQ-004 (Security - Foundational):**
    *   Backend API endpoints will rely on the current placeholder authentication for MVP development.
    *   S3 bucket policies should be configured for appropriate access control.
    *   **User Data Control:** Users must have the option to explicitly save their analysis runs and datasets for future access or choose to have them be session-based/temporary (with clear prompts for deletion or persistence). This is a key security and user-choice feature.
    *   Awareness of future needs: full ORCID-based authentication, authorization to ensure data privacy (users access only their projects/data), protection against common web vulnerabilities (OWASP Top 10).

## 4. Future Features & Considerations (Post-MVP for BenchTop)

### 4.1. Broad Technique & Tool Expansion
*   Aggressively expand support for a wide array of tools and techniques across various biological science domains (e.g., single-cell RNA-seq, proteomics, metabolomics, calcium imaging, electrophysiology, flow cytometry, advanced microscopy analysis).
*   The architecture (YAML configs, modular backend processors) is designed to facilitate this expansion beyond just omics.
*   Advanced customization options for plots (colors, fonts, layouts, annotations) for all tools.
*   Interactive plot elements (zooming, panning, point selection, data brushing).
*   Support for more complex experimental designs in parameter inputs across all techniques.

### 4.2. Image Analysis Workbench (e.g., "ImageWorkbench", "FigureForge")
*   Dedicated workspace for Fiji/ImageJ-like image processing, integrated seamlessly yet distinctly within BenchTop.
*   Features: ROI management, macro recording/playback, cell segmentation (Cellpose, Stardist), batch processing, intensity measurements, 3D rendering.

### 4.3. AI Copilots & Social Integration
*   **BenchTop AI:** Suggestions for statistical tests, flagging outliers, auto-generation of figure captions/method summaries, natural language queries for data exploration.
*   **BenchMate Social AI:** When BenchTop analyses are shared to BenchMate (the social platform), AI can help summarize findings for a broader audience, suggest relevant researchers or discussions, and facilitate interdisciplinary discovery based on shared data or research interests.

### 4.4. Collaboration & Sharing
*   **BenchTop:** Sharing analyses/results with collaborators (read-only, edit access), version history, export of pipelines/notebooks.
*   **BenchMate Integration:** Seamless "Share to BenchMate" functionality for BenchTop outputs, allowing users to post their findings, figures, and data summaries to their BenchMate profile or relevant community groups.

### 4.5. Enhanced Security & User Control
*   Full implementation of ORCID/Supabase authentication (shared with BenchMate social).
*   Role-based access control (RBAC) within projects.
*   Granular user control over data persistence, sharing permissions, and data deletion.
*   Audit trails for data and analysis modifications.
*   Compliance with relevant data privacy regulations.

## 5. Data Objects & Schema (Brief Overview - Refer to Backend Models)
*   **User:** Profile, ORCID, role, plan.
*   **Project:** Name, members, datasets, analysis runs, visibility.
*   **Dataset:** File metadata, S3 storage pointer, technique type, associated project/user.
*   **AnalysisRun:** Input dataset(s), tool ID, parameters, status, output artifacts (S3 paths, summaries), logs, associated project/user.
*   (Refer to `backend/app/models/` for detailed SQLAlchemy definitions).

## 6. Technical Stack Overview (BenchTop MVP)
*   **Frontend:** Next.js (v15+), React (v19+), TypeScript, Tailwind CSS, shadcn/ui.
*   **Backend:** Python (v3.12), FastAPI, Celery, Uvicorn.
*   **Data Stores:** PostgreSQL (metadata), MinIO/S3 (file blobs), Redis (Celery broker/backend).
*   **Key Python Libraries (Initial):** Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn, openpyxl, (domain-specific: Scanpy, etc., as new tools are added). The full list is in `backend/requirements_biology.txt`.
*   **Configuration:** YAML for tool definitions.
*   **DevOps:** Docker, Docker Compose, GitHub Actions (CI).

## 7. Open Questions & Decisions for MVP
*   Specific list of parameters and basic manipulations for the foundational ImageJ/Fiji workbench features (e.g., what quantitative data can be extracted initially?).
*   Default behavior for data/analysis run persistence (e.g., prompt to save after X duration, or always require explicit save).
*   Initial set of "technique types" the data upload component will recognize or allow users to specify.
*   Technical approach for interactive plot refinement on the frontend (e.g., client-side Plotly.js capabilities vs. backend re-rendering).

## 8. Glossary
*   **BenchMate:** The overarching platform including social and tool aspects.
*   **BenchTop:** The analytical workbench component of BenchMate.
*   **MVP:** Minimum Viable Product.
*   **Bulk RNA-seq:** Bulk RNA sequencing.
*   **PCA:** Principal Component Analysis.
*   **ORCID:** Open Researcher and Contributor ID.
*   **S3:** Simple Storage Service (object storage, MinIO provides compatibility).
*   **YAML:** YAML Ain't Markup Language (human-readable data serialization).

---
*(End of PRD Version 0.3)*