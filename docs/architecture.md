# Overview of the architecture and integration plan

BENCHMATE-MVP # Root project folder
├── backend # Contains all backend-related code and configurations
│   ├── app # Core application code for the backend API
│   │   ├── config  # YAML configuration files for default tool settings
│   │   │   ├── benchsocial
│   │   │   │   └── homepage.yaml
│   │   │   ├── benchtop
│   │   │   │   ├── homepage.yaml
│   │   │   │   └── biology
│   │   |   │       ├── calcium_imaging
│   │   |   │       ├── electrophysiology
│   │   |   │       ├── flow_cytometry
│   │   |   │       ├── imaging
│   │   |   │       ├── medical
│   │   |   │       └── omics
│   │   |   │           ├── metabolomics
│   │   |   │           ├── proteomics
│   │   |   │           └── transcriptomics
│   │   |   │               └── bulk_rna_seq
│   │   |   │                   └── volcano.yaml
│   │   │   ├── homepage.yaml
│   │   │   ├── README.md
│   │   │   └── shared
│   │   ├── endpoints # API endpoint modules; each file here implements a set of related API routes
│   │   │   ├── benchsocial
│   │   │   ├── benchtop
│   │   │   │   └── biology
│   │   │   │       ├── calcium_imaging
│   │   │   │       ├── electrophysiology
│   │   │   │       ├── flow_cytometry
│   │   │   │       ├── imaging
│   │   │   │       ├── medical
│   │   │   │       └── omics
│   │   │   │           ├── metabolomics
│   │   │   │           ├── proteomics
│   │   │   │           └── transcriptomics
│   │   │   │               └── bulk_rna_seq
│   │   │   │                   └── volcano.py
│   │   │   ├── integration
│   │   │   └── README.md
│   │   └── utils # Helper functions
│   │       ├── benchsocial
│   │       ├── benchtop
│   │       │   └── biology
│   │       │       ├── calcium_imaging
│   │       │       ├── electrophysiology
│   │       │       ├── flow-cytometry
│   │       │       ├── imaging
│   │       │       ├── medical
│   │       │       └── omics
│   │       │           ├── metabolomics
│   │       │           ├── proteomics
│   │       │           └── transcriptomics
│   │       │               └── bulk-rna-seq
│   │       │                   └── volcano_processor.py
│   │       ├── config_loader.py
│   │       └── README.md
│   ├── main.py
│   └── requirements.txt # List of Python packages specific to the backend
├── docs
│   └── architecture.md
├── env
├── frontend # This is where the React project will be set up
│   ├── benchsocial
│   │   ├── public
│   │   └── src
│   │       ├── components
│   │       └── app.js
│   ├── packages-json
│   │   ├── benchsocial
│   │   ├── benchtop
│   │   │   └── biology
│   │   │       ├── calcium_imaging
│   │   │       ├── electrophysiology
│   │   │       ├── flow_cytometry
│   │   │       ├── imaging
│   │   │       ├── medical
│   │   │       └── omics
│   │   │           ├── metabolomics
│   │   │           ├── proteomics
│   │   │           └── transcriptomics
│   │   │               └── bulk_rna_seq
│   │   └── shared
│   └── benchtop/
│       ├── public/
│       │   └── index.html         // The HTML entry point for your app.
│       └── src/
│           ├── app.js             // Main React entry point; sets up routing, theme, etc.
│           ├── index.js           // ReactDOM.render(...) to start the app.
│           ├── components/        // Reusable components across pages.
│           │   ├── common/        // Shared UI components (e.g., FileUpload, Button, Input, Dropdown).
│           │   └── homepage/      // Components specific to the homepage (e.g., Banner, ToolSelector).
│           ├── pages/             // Different pages or sections by domain.
│           │   ├── homepage.js    // A page that aggregates multiple homepage components.
│           │   └── biology/
│           │       └── omics/
│           │           └── transcriptomics/
│           │               └── bulk_rna_seq/
│           │                   ├── VolcanoPlot.js       // Displays the volcano plot visualization.
│           │                   ├── ColumnMapping.js     // Lets users select/override column mappings.
│           │                   ├── VisualizationOptions.js  // Optional: additional plotting options (e.g., thresholds).
│           │                   └── DataSummary.js       // Optional: display summary stats.
│           ├── services/          // Utility layer for API communication.
│           │   └── api.js         // Contains helper functions to make HTTP requests to the backend.
│           └── styles/            // (Optional) Global or component-specific CSS/SCSS files.
├── tests
│   ├── backend
│   └── frontend
├── .gitignore
└── README.md # Project overview, setup instructions, and documentation for the overall architecture
