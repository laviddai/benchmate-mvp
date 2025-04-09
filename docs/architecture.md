# Overview of the architecture and integration plan

BENCHMATE-MVP
├── backend
│   ├── app
│   │   ├── config
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
│   │   │   ├── README.md
│   │   │   └── shared
│   │   ├── endpoints
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
│   │   │   │                   └── bulk_rna_seq_volcano.py
│   │   │   ├── integration
│   │   │   └── README.md
│   │   └── utils
│   │       ├── benchsocial
│   │       ├── benchtop
│   │       │   └── biology
│   │       │       ├── calcium_imaging
│   │       │       ├── electrophysiology
│   │       │       ├── flow_cytometry
│   │       │       ├── imaging
│   │       │       ├── medical
│   │       │       └── omics
│   │       │           ├── metabolomics
│   │       │           ├── proteomics
│   │       │           └── transcriptomics
│   │       │               └── bulk_rna_seq
│   │       └── README.md
│   ├── main.py
│   └── requirements.txt
├── docs
│   └── architecture.md
├── env
├── frontend
│   ├── benchsocial
│   │   ├── public
│   │   └── src
│   │       ├── components
│   │       └── app.js
│   ├── benchtop
│   │   ├── public
│   │   └── src
│   │       ├── components
│   │       └── app.js
│   └── packages-json
│       ├── benchsocial
│       ├── benchtop
│       │   └── biology
│       │       ├── calcium_imaging
│       │       ├── electrophysiology
│       │       ├── flow_cytometry
│       │       ├── imaging
│       │       ├── medical
│       │       └── omics
│       │           ├── metabolomics
│       │           ├── proteomics
│       │           └── transcriptomics
│       │               └── bulk_rna_seq
│       └── shared
├── .gitignore
└── README.md
