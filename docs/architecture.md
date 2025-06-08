# BenchMate Platform Architecture

**Version:** 0.2
**Date:** June 7, 2025
**Status:** In Development (Reflecting BenchTop MVP)

## 1. Overview

This document describes the technical architecture of the BenchMate platform, which comprises two main components:
*   **BenchTop:** An interactive analytical workbench designed for researchers to upload data, perform complex analyses, generate publication-quality visualizations, and manage their scientific workflows. This is the primary focus of the current MVP.
*   **BenchMate (Social):** A future collaborative social platform for the scientific community to share findings, ask questions, and network. It will integrate with BenchTop.

The architecture is designed to be modular, scalable, and maintainable, supporting a wide range of scientific data types and analytical tools. It leverages a modern technology stack including a Python/FastAPI backend for robust computation and a Next.js/React frontend for a dynamic user experience.

## 2. Guiding Architectural Principles

*   **Modularity:** Components are designed as loosely coupled services or modules to allow independent development, deployment, and scaling.
*   **Scalability:** The system is architected to handle increasing numbers of users, data volume, and computational load, primarily through asynchronous task processing and scalable backend services.
*   **Extensibility:** New scientific tools, data types, and features can be added with minimal changes to the core system, largely driven by YAML configurations.
*   **Separation of Concerns:** Clear distinction between the presentation layer (frontend), application logic (backend API), asynchronous task processing (Celery workers), and data persistence.
*   **Security by Design:** Incorporating security considerations at each layer, from authentication and authorization to data storage and transmission.
*   **User-Centricity:** Focusing on providing an intuitive and efficient user experience for researchers with varying levels of computational expertise.

## 3. High-Level System Architecture

The BenchMate platform, focusing on the BenchTop MVP, consists of the following key layers and components:
+----------------------+ +------------------------+ +-----------------------+
| Frontend | --> | Backend API Server | --> | Asynchronous Task |
| (Next.js/React) | | (FastAPI) | | Processing Layer |
| - UI/UX | | - Request Handling | | (Celery & Redis) |
| - API Client | | - Business Logic | | - Long-running Analyses|
| - Visualization | | - Auth (placeholder) | | - Data Processing |
| Rendering | | - Config Loading | | |
+----------------------+ +----------+-------------+ +-----------+-----------+
| |
| |
v v
+----------------------+ +------------------------+ +-----------------------+
| Data Stores | <-- | Object Storage | | Configuration |
| (PostgreSQL) | | (MinIO/S3) | | (YAML Files) |
| - User Metadata | | - Raw Datasets | | - Tool Definitions |
| - Project Metadata | | - Analysis Results | | - Default Parameters |
| - Analysis Run Info | | (Plots, Tables) | | |
+----------------------+ +------------------------+ +-----------------------+

### 3.1. Frontend (BenchTop Client)
*   **Technology:** Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui.
*   **Responsibilities:**
    *   Providing the user interface for data upload, project management, analysis selection, parameter input, and results visualization.
    *   Making API calls to the Backend API Server.
    *   Rendering interactive visualizations (e.g., using Plotly.js, Recharts, or rendering images served from the backend).
    *   Client-side state management (e.g., Zustand or Redux Toolkit, if needed beyond Next.js capabilities).
*   **Location:** `frontend/benchtop-nextjs/`

### 3.2. Backend API Server (BenchTop API)
*   **Technology:** Python, FastAPI, Uvicorn.
*   **Responsibilities:**
    *   Exposing RESTful API endpoints for frontend interactions.
    *   Handling user authentication and authorization (currently placeholder, future ORCID/Supabase integration).
    *   Validating incoming requests and data.
    *   Orchestrating core business logic:
        *   Managing users, projects, datasets, and analysis runs (CRUD operations via `app/crud/`).
        *   Interfacing with PostgreSQL for metadata storage.
        *   Interfacing with MinIO/S3 for file storage (uploads, presigned URLs via `app/services/s3_service.py`).
        *   Loading tool configurations from YAML files (`app/utils/config_loader.py`).
        *   Submitting long-running analysis jobs to the Celery task queue.
*   **Location:** `backend/`

### 3.3. Asynchronous Task Processing Layer
*   **Technology:** Celery, Redis (as message broker and result backend).
*   **Responsibilities:**
    *   Executing computationally intensive and long-running tasks asynchronously, such as:
        *   Data preprocessing.
        *   Running scientific analysis pipelines (e.g., `volcano_processor.py` for bulk RNA-seq).
        *   Generating visualizations.
        *   Image processing tasks (future).
    *   Updating the status and results of `AnalysisRun` records in PostgreSQL upon task completion or failure.
    *   Interacting with MinIO/S3 to fetch input data and store output results.
*   **Location:** `backend/app/celery_worker.py`

### 3.4. Data Stores
*   **PostgreSQL (Relational Database):**
    *   **Purpose:** Storing structured metadata.
    *   **Schema:** Includes tables for `users`, `projects`, `project_members`, `datasets`, `analysis_runs`. Managed by SQLAlchemy ORM and Alembic for migrations.
    *   **Location:** Defined in `backend/app/models/` and `backend/app/db/`.
*   **MinIO/S3 (Object Storage):**
    *   **Purpose:** Storing large binary data (file blobs).
    *   **Content:** Raw uploaded datasets, intermediate processed files, final analysis results (plots, tables, images).
    *   **Access:** Managed by `app/services/s3_service.py`, utilizing presigned URLs for secure client access where appropriate.

### 3.5. Configuration System
*   **Technology:** YAML files.
*   **Purpose:** Defining parameters, behaviors, and UI elements for different scientific tools and techniques. This allows for dynamic tool generation and easy extensibility.
    *   Expected input data formats and column names.
    *   Default analysis parameters (e.g., thresholds).
    *   Available visualizations and their default settings.
    *   UI control definitions for parameter input.
*   **Location:** `backend/app/config/` (organized by domain, e.g., `benchtop/biology/omics/transcriptomics/`).

## 4. Detailed Component Interactions (BenchTop MVP Workflow Example: Volcano Plot)

1.  **User Uploads Data (Frontend):**
    *   User selects a project and uploads a CSV/TSV file via the Next.js UI.
    *   Frontend sends a `POST` request to `/api/datasets/upload-and-create/` (FastAPI).
2.  **Dataset Creation (Backend API):**
    *   FastAPI endpoint receives the file and metadata.
    *   `s3_service` uploads the file to MinIO.
    *   `crud_dataset` creates a `Dataset` record in PostgreSQL with the S3 path and metadata.
    *   API returns success response to the frontend.
3.  **User Configures & Submits Analysis (Frontend):**
    *   User selects the uploaded dataset and chooses "Volcano Plot" analysis.
    *   User inputs parameters (gene column, LFC column, p-value column, thresholds) in the Next.js UI.
    *   Frontend sends a `POST` request to `/api/analyses/volcano-plot/submit` with dataset ID and parameters.
4.  **Analysis Job Initiation (Backend API):**
    *   FastAPI endpoint validates input.
    *   `crud_analysis_run` creates an `AnalysisRun` record in PostgreSQL with `status: PENDING` and parameters.
    *   The endpoint enqueues a Celery task (`run_volcano_plot_analysis`) with `analysis_run_id`, dataset S3 path, and parameters.
    *   API returns the `AnalysisRun` object (with PENDING status) to the frontend.
5.  **Asynchronous Processing (Celery Worker):**
    *   Celery worker picks up the task from the Redis queue.
    *   Worker updates `AnalysisRun` status to `RUNNING` in PostgreSQL.
    *   Worker downloads input dataset from MinIO using `s3_service`.
    *   Worker executes `volcano_processor.py` logic:
        *   Loads data (Pandas).
        *   Preprocesses data.
        *   Generates plot (Matplotlib).
    *   Worker uploads the resulting plot image to MinIO via `s3_service`.
    *   Worker updates `AnalysisRun` status to `COMPLETED` (or `FAILED`) in PostgreSQL, storing S3 path of the plot and any summary/log.
6.  **Status Polling & Result Display (Frontend):**
    *   Frontend periodically polls `GET /api/analysis-runs/{analysis_run_id}`.
    *   Once status is `COMPLETED`, frontend retrieves the `output_artifacts` (including plot S3 path).
    *   Frontend requests a presigned URL for the plot image from `GET /api/files/presigned-url/`.
    *   Frontend displays the plot image using the presigned URL and allows for user refinement (adjusting legends, titles, etc., potentially via client-side libraries or further backend calls for re-rendering).
    *   User can extract relevant data (e.g., gene lists).
    *   User can export the refined plot and data.

## 5. Directory Structure Overview

*   **`backend/`**: FastAPI application, Celery worker, database models, CRUD operations, API endpoints, services, utility functions, and tool configurations (YAML).
    *   **`backend/app/api/`**: Defines API routers and endpoints.
    *   **`backend/app/crud/`**: Data access logic for database models.
    *   **`backend/app/models/`**: SQLAlchemy ORM models.
    *   **`backend/app/schemas/`**: Pydantic schemas for data validation and serialization.
    *   **`backend/app/services/`**: Business logic for specific services (e.g., S3 interaction).
    *   **`backend/app/utils/`**: Helper functions and core processing logic for tools (e.g., `volcano_processor.py`).
    *   **`backend/app/config/`**: YAML configurations for tools.
    *   **`backend/celery_worker.py`**: Celery task definitions.
    *   **`backend/main.py`**: FastAPI application entry point.
*   **`frontend/benchtop-nextjs/`**: Next.js application for the BenchTop UI.
    *   **`frontend/benchtop-nextjs/src/app/`**: Core application pages and layouts (App Router).
    *   **`frontend/benchtop-nextjs/src/components/`**: Reusable UI components (including shadcn/ui).
    *   **`frontend/benchtop-nextjs/src/lib/`**: Utility functions for the frontend.
    *   **`frontend/benchtop-nextjs/src/services/` (To Be Created):** API client functions.
*   **`docs/`**: Project documentation (including this `architecture.md`, `prd.md`, `white_paper.md`).
*   **`.devcontainer/`**: Dev container configuration for Codespaces.
*   **`.github/workflows/`**: CI/CD pipelines using GitHub Actions.
*   **`docker-compose.yaml`**: Defines and orchestrates the local development environment services (backend, celeryworker, postgres, redis, minio).

## 6. Future Architectural Considerations

### 6.1. Image Analysis Workbench Integration
*   A dedicated module within BenchTop, potentially named "ImageWorkbench" or "FigureForge".
*   Will require specific backend services for handling image processing tasks (interfacing with Fiji/ImageJ via PyImageJ, Cellpose, Stardist).
*   May involve a more complex frontend UI for interactive image manipulation, ROI selection, and macro building.
*   Could leverage WASM for client-side image processing capabilities to reduce server load for certain operations.

### 6.2. AI Copilot Integration
*   Backend services for interfacing with AI models (e.g., HuggingFace, OpenAI).
*   Potential use of vector databases for semantic search over scientific literature or user-generated content (in BenchMate social).
*   APIs to provide suggestions, explanations, and automated content generation to the frontend.

### 6.3. BenchMate Social Platform Integration
*   Shared authentication (likely via Supabase, with BenchTop validating Supabase JWTs or using ORCID as a common IdP).
*   APIs for BenchTop to push analysis summaries/links to BenchMate.
*   Frontend components in BenchTop to trigger "Share to BenchMate" actions.

### 6.4. Enhanced Security
*   Implementation of robust authentication (ORCID via Supabase).
*   Fine-grained authorization and Role-Based Access Control (RBAC) for projects and data.
*   Encryption at rest and in transit for all sensitive data.
*   Regular security audits and adherence to OWASP best practices.
*   Mechanisms for user data consent, management (including deletion), and compliance with data privacy regulations (GDPR, HIPAA where applicable).

### 6.5. Scalability & Performance
*   Further optimization of Celery workers (e.g., multiple queues for different task types, dynamic scaling of workers).
*   Database query optimization and potential use of read replicas for PostgreSQL.
*   Caching strategies (e.g., Redis for frequently accessed data, CDN for static assets).
*   Consideration of microservices for highly specialized or resource-intensive tools if the modular monolith approach becomes a bottleneck.

## 7. Technology Choices Rationale (Summary)

*   **Python/FastAPI (Backend):** Excellent for rapid API development, strong performance, large ecosystem of scientific libraries, asynchronous capabilities.
*   **Celery (Task Queue):** Industry standard for distributed task queues, handles long-running computations effectively.
*   **Next.js/React (Frontend):** Modern, performant framework for building interactive UIs, strong community support, server-side rendering and static site generation capabilities.
*   **PostgreSQL (Database):** Robust, open-source relational database with good support for complex queries and JSON data types.
*   **MinIO/S3 (Object Storage):** Scalable and cost-effective for storing large files.
*   **Docker/Docker Compose:** Standard for containerization, ensuring consistent development and deployment environments.
*   **YAML (Configuration):** Human-readable and easy to manage for defining tool parameters and behaviors.

---
*(End of Architecture Document v0.2)*