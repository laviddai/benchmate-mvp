# BenchMate-MVP

Welcome to BenchMate-MVP, the scalable, modular platform that brings together innovative researcher tools with a social collaboration layer for the scientific community. This private repository houses the next-generation version of BenchMate. The system is designed to support data-intensive analysis, interactive visualizations, and social engagement, all built on a robust asynchronous backend (Python with FastAPI) and dynamic frontend applications (React).

## Overview

BenchMate-MVP consists of two primary components:

- **BenchTop:**  
  A suite of powerful research tools for data analysis and visualization (e.g., the Volcano Plot tool for bulk RNA-seq analysis). This part of the platform empowers researchers to process, visualize, and share their data analyses.

- **BenchSocial:**  
  A dedicated social platform for scientists to share insights, collaborate, and engage with a broader community. BenchSocial integrates with BenchTop so that users can easily post and discuss their analytical results.

Additionally, the project uses YAML configurations to define tool behavior and settings, which are parsed by the backend and served to the frontend as JSON.

## Key Features

- **Modular Architecture:**  
  Separate backend and frontend projects organized by domain, ensuring each component can be developed and scaled independently.

- **Domain Separation:**  
  Dedicated directories and endpoints for both BenchTop (researcher tools) and BenchSocial (social platform).

- **Asynchronous Backend API:**  
  Built using FastAPI and Uvicorn to efficiently handle large data volumes and simultaneous API requests.

- **Dynamic UI/UX:**  
  React-based frontends for both researcher tools and the social platform, designed for a consistent and engaging user experience.

- **Configurable Defaults:**  
  YAML configuration files provide a human-friendly way to set defaults and parameters, which are easily updated or overridden by users.

- **Scalability:**  
  A folder structure and codebase designed to support future features including desktop apps, mobile apps, and AI integration.

## Folder Structure

Below is an overview of the project’s directory structure:

```
BenchMate-MVP/
├── backend/                         # Python backend API
│   ├── app/
│   │   ├── config/                  # YAML configuration files
│   │   │   ├── benchsocial          # Social platform-specific configs (e.g., homepage.yaml)
│   │   │   ├── benchtop             # Research tools-specific configs (homepage.yaml, biology configs, etc.)
│   │   │   └── shared               # Configurations shared across domains
│   │   ├── endpoints/               # API endpoints organized by domain
│   │   │   ├── benchsocial          # Social endpoints (e.g., posts, comments)
│   │   │   ├── benchtop             # Research tool endpoints (e.g., biology tools)
│   │   │   │   └── biology          # Further breakdown for biology subdomains (calcium_imaging, electrophysiology, etc.)
│   │   │   ├── integration          # Endpoints bridging BenchTop and BenchSocial functionality
│   │   │   └── README.md            # Documentation for endpoints
│   │   └── utils/                   # Shared utilities (e.g., configuration loaders, authentication helpers)
│   │       ├── benchsocial
│   │       ├── benchtop
│   │       └── README.md
│   ├── main.py                      # Backend API entry point (FastAPI app)
│   └── requirements.txt             # Python dependencies for the backend
├── docs/                            # Documentation (architecture diagrams, integration plan, etc.)
│   └── architecture.md
├── env/                             # Virtual environment folder (should be ignored by Git)
├── frontend/                        # Frontend projects
│   ├── benchsocial/                 # React app for the social platform
│   │   ├── public/                  # Public assets (HTML, images, etc.)
│   │   └── src/                     # Source code for BenchSocial UI
│   │       ├── components/          # Reusable components
│   │       └── app.js               # Main React component for BenchSocial
│   ├── benchtop/                    # React app for researcher tools
│   │   ├── public/                  # Public assets for BenchTop
│   │   └── src/                     # Source code for BenchTop UI
│   │       ├── components/          # Reusable UI components (e.g., TooltipGuide, VisualizationPage)
│   │       └── app.js               # Main React component for BenchTop
│   └── packages-json/               # Package.json files organized by domain (including shared configurations)
├── .gitignore                       # Files and folders to ignore in Git (e.g., env/, node_modules/)
└── README.md                        # This README file
```

## Getting Started

### Prerequisites

- **Python 3.8+**  
- **Node.js and npm** (for React apps)
- **Git** (for version control)
- A code editor like **VSCode**

### Setting Up the Backend

1. **Clone the Repository**  
   ```bash
   git clone <repository-url>
   cd BenchMate-MVP/backend
   ```

2. **Create and Activate a Virtual Environment**  
   ```bash
   python -m venv env
   # On Windows:
   .\env\Scripts\activate
   # On macOS/Linux:
   source env/bin/activate
   ```

3. **Install Python Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Backend Server**  
   For example, if using FastAPI with Uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```

### Setting Up the Frontend

Each frontend project (BenchSocial and BenchTop) is a separate React application.

1. **Navigate to the Frontend Directory**  
   ```bash
   cd BenchMate-MVP/frontend/benchtop
   npm install
   npm start
   ```
   Repeat for the BenchSocial project if needed.

2. **Shared Package Configurations:**  
   The `packages-json` folder contains individual package.json files for specialized parts of your frontend. Adjust these as necessary based on your project needs.

## Architecture & Integration

Our system is designed with clear separation of concerns:

- **Backend API:**  
  Manages data processing, configuration management (via YAML), and serves endpoints for both the researcher tools (BenchTop) and social features (BenchSocial).

- **Frontend Applications:**  
  Independently built React apps tailored to specific user groups while sharing common components and configurations where applicable.

- **Integration Points:**  
  When an analysis result from BenchTop needs to be shared on BenchSocial, our integration endpoints or frontend coordination ensures smooth data flow and interaction between these domains.

For a detailed architecture overview, see the [docs/architecture.md](docs/architecture.md) file.

## Contributing

This repository is private. However, for team members with access:

1. **Fork the repository and work on feature branches.**
2. **Ensure you adhere to the coding standards outlined in our documentation.**
3. **Write unit tests for new features and ensure all tests pass before merging.**
4. **Update documentation (README, architecture docs, etc.) as necessary.**

## Onboarding & Documentation

- **Onboarding Guides:**  
  Refer to the [docs/architecture.md](docs/architecture.md) for a complete overview of our integration plan, folder structure, and module responsibilities.

- **Additional Documentation:**  
  Each major folder (backend endpoints, utils, and frontend modules) contains its own README for further details on usage and conventions.

## License

N/A

## Contact

N/A
