# API Endpoints Directory

This directory contains the API endpoint modules for BenchMate-MVP. The endpoints are organized by domain to clearly separate functionality between the research tools (BenchTop) and the social platform (BenchSocial).

## Domain-Specific Folders

- **benchsocial/**:  
  Contains endpoints dedicated to the social platform. These endpoints handle operations such as posting updates, managing user interactions, retrieving social feeds, and processing comments.

- **benchtop/**:  
  Contains endpoints for the researcher tools. For example, endpoints for biology-related tools reside here, including subfolders for specialized domains such as:
  - **biology/calcium_imaging**  
  - **biology/electrophysiology**  
  - **biology/flow_cytometry**  
  - **biology/imaging**  
  - **biology/medical**  
  - **biology/omics** (which further includes metabolomics, proteomics, and transcriptomics)

- **integration/**:  
  Contains endpoints that bridge functionality between BenchTop and BenchSocial. These may be used when sharing analysis results from research tools (BenchTop) onto the social platform (BenchSocial).

## How It Works

- **Modularity:**  
  Each endpoint module is responsible for a specific set of operations and is imported and mounted on the main API application (located in `backend/app/main.py`).

- **Documentation & Conventions:**  
  Each subfolder (and individual endpoint module) should be documented with inline code comments. Refer to this README for an overview of the folder structure and its intended responsibilities.

- **Extending Endpoints:**  
  When adding new endpoints, follow the existing structure by placing them in the appropriate domain folder to maintain consistency and clarity.

For a complete overview of how the backend integrates with the frontend and configuration settings, please refer to the main project README and the documentation in the `docs/` folder.
