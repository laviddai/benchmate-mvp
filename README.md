# BenchMate: A Unified Platform for Scientific Analysis, Visualization, and Collaboration

**Status:** Actively In Development (Focusing on BenchTop MVP)

Welcome to the BenchMate repository. BenchMate is a scalable, modular platform designed to bring together innovative researcher tools (**BenchTop**) with a collaborative social layer (**BenchMate Social**) for the scientific community. The system supports data-intensive analysis, interactive visualizations with publication-quality output, and aims to foster scientific engagement, all built on a robust asynchronous backend (Python with FastAPI) and a dynamic frontend (Next.js/React for BenchTop).

## 1. Overview

BenchMate consists of two primary, integrated components:

*   **BenchTop (Current MVP Focus):**  
    An interactive analytical workbench empowering researchers to:
    *   Upload and manage diverse scientific data (MVP starting with bulk RNA-seq and foundational imaging).
    *   Perform complex analyses without requiring coding expertise.
    *   Generate and refine publication-quality visualizations.
    *   Utilize a growing library of tools driven by a flexible YAML configuration system.

*   **BenchMate Social (Parallel Development for Future Integration):**  
    A dedicated social platform for scientists to:
    *   Share insights, analyses, and results from BenchTop.
    *   Collaborate within and across disciplines.
    *   Engage with a broader scientific community and the public.
    *   (Planned Backend: Supabase)

## 2. Key Features & Goals

*   **Unified Workspace:** Seamlessly integrate data analysis, visualization, and (future) collaboration.
*   **Accessible Power:** Make sophisticated scientific tools available to researchers regardless of coding skill, via an intuitive UI.
*   **Publication-Quality Outputs:** Enable users to generate and customize figures and tables suitable for scientific publications.
*   **Modular & Extensible Architecture:** Easily add new scientific domains, techniques, and tools (primarily in BenchTop via YAML configs).
*   **Reproducibility:** Facilitate reproducible research by logging parameters and workflows.
*   **Asynchronous Backend:** Efficiently handle computationally intensive tasks using FastAPI and Celery.
*   **Modern Frontend:** Dynamic and responsive user experience with Next.js and React for BenchTop.
*   **AI-Assisted Guidance (Future):** Incorporate AI to aid in tool selection, parameter optimization, and result interpretation.
*   **Collaborative Environment (Future):** Foster interdisciplinary work and science communication through BenchMate Social.

## 3. Getting Started

### 3.1. Prerequisites
*   Python 3.12+
*   Node.js (v18+ recommended for Next.js) & npm/yarn/pnpm
*   Docker & Docker Compose
*   Git
*   A code editor like VSCode (recommended with Dev Containers for an optimized setup).

### 3.2. Recommended Setup (Dev Container / Codespaces)
This repository is configured for use with [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers) or [GitHub Codespaces](https://github.com/features/codespaces).
1.  If using VS Code locally, ensure you have the "Dev Containers" extension installed.
2.  Open the repository in VS Code. You should be prompted to "Reopen in Container". Click it.
3.  This will build the development environment as defined in `.devcontainer/devcontainer.json` and `.devcontainer/Dockerfile`.
4.  The `postCreateCommand` will install backend Python dependencies and frontend Node modules.
5.  Ports for the frontend (3000) and backend (8000) will be automatically forwarded.

### 3.3. Local Setup (using Docker Compose)
If not using Dev Containers, you can run the services using Docker Compose:
1.  Clone the repository: `git clone <repository-url> && cd BenchMate`
2.  Ensure Docker Desktop (or Docker Engine with Docker Compose plugin) is running.
3.  Build and start the services:
    ```bash
    docker compose up --build -d
    ```
    *   This will start the backend API, Celery worker, PostgreSQL, Redis, and MinIO.
    *   The backend API will be available at `http://localhost:8000`.
    *   MinIO console will be available at `http://localhost:9001`.
4.  To run the **BenchTop frontend** (Next.js) development server:
    ```bash
    cd frontend/benchtop-nextjs
    npm install # Or yarn install / pnpm install
    npm run dev
    ```
    *   The BenchTop frontend will be available at `http://localhost:3000`.

### 3.4. Local Setup (Manual - Alternative, more complex)

**Backend (FastAPI):**
1.  Navigate to `backend/`.
2.  Create and activate a Python virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate # macOS/Linux
    # .\.venv\Scripts\activate # Windows
    ```
3.  Install dependencies: `pip install -r requirements_biology.txt`
4.  Ensure PostgreSQL, Redis, and MinIO are running and accessible, and configure environment variables (e.g., in a `.env` file in `backend/`) for `DATABASE_URL`, `S3_ENDPOINT_URL`, etc.
5.  Run the FastAPI development server: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
6.  Run the Celery worker in a separate terminal: `celery -A app.celery_worker worker -l INFO`

**Frontend (BenchTop - Next.js):**
1.  Navigate to `frontend/benchtop-nextjs/`.
2.  Install dependencies: `npm install`
3.  Run the development server: `npm run dev`

*(Note: The Docker Compose or Dev Container methods are highly recommended for a consistent development experience.)*

## 4. Project Structure Overview

The repository is organized into several key directories:

*   **`backend/`**: Contains the Python FastAPI application for BenchTop's API, Celery workers, database models, analysis processing scripts, and tool configurations (YAML).
*   **`frontend/benchtop-nextjs/`**: Contains the Next.js/React application for the BenchTop user interface.
*   **`docs/`**: Houses detailed project documentation:
    *   [`docs/prd.md`](./docs/prd.md): Product Requirements Document.
    *   [`docs/architecture.md`](./docs/architecture.md): System Architecture Document.
    *   [`docs/white_paper.md`](./docs/white_paper.md): Project White Paper.
*   **`.devcontainer/`**: Configuration for VS Code Dev Containers and GitHub Codespaces.
*   **`.github/workflows/`**: CI/CD pipelines using GitHub Actions for automated testing and builds.
*   **`docker-compose.yaml`**: Defines the multi-container local development environment.
*   **`tests/`**: Contains backend and (future) frontend tests.

*(For a more granular breakdown of the `backend` and `frontend` subdirectories, please refer to `docs/architecture.md#5-directory-structure-overview`.)*

## 5. Core Technologies

*   **Backend:** Python, FastAPI, Celery, SQLAlchemy, PostgreSQL, Redis, MinIO (S3-compatible).
*   **Frontend (BenchTop):** Next.js, React, TypeScript, Tailwind CSS, shadcn/ui.
*   **Configuration:** YAML.
*   **DevOps:** Docker, Docker Compose, GitHub Actions.

## 6. Documentation Suite

For a comprehensive understanding of the BenchMate platform, please refer to our detailed documentation:

*   **Product Requirements (What & Why):** [`docs/prd.md`](./docs/prd.md)
    *   *Key Sections for Understanding Current Focus:* Section 1 (Introduction & Vision), Section 3 (BenchTop MVP: Demonstrating a Generalizable Workflow).
*   **System Architecture (How):** [`docs/architecture.md`](./docs/architecture.md)
    *   *Key Sections for Technical Overview:* Section 3 (High-Level System Architecture), Section 4 (Detailed Component Interactions).
*   **Project Vision & Impact (Broader Context):** [`docs/white_paper.md`](./docs/white_paper.md)
    *   *Key Sections for Overall Goals:* Section 2 (Introduction), Section 3 (The BenchMate Solution).

These documents provide the full context for development, features, and future roadmap.

## 7. Contributing

This is currently a private repository. For team members:
1.  Create feature branches from `main` (or the designated development branch).
2.  Follow established coding standards and practices.
3.  Ensure new code is accompanied by relevant tests.
4.  Update documentation (PRD, Architecture, READMEs) as features evolve.
5.  Submit Pull Requests for review and merging.

## 8. License

Currently proprietary. (Placeholder - update as needed)

## 9. Contact

(Placeholder - update as needed)