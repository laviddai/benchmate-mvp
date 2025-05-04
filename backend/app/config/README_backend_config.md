# Configuration Directory

This directory contains YAML configuration files used by the BenchMate-MVP backend to set default parameters and tool settings. These configurations are written in human-friendly YAML format and are organized by domain:

- **benchsocial/**:  
  Contains configuration files specific to the social platform (e.g., homepage.yaml for BenchSocial). Use these files to define settings for social interactions and common UI defaults for the social module.

- **benchtop/**:  
  Contains configuration files for the researcher tools (e.g., homepage.yaml, and the biology subdirectory for specialized tool configurations such as bulk RNA-seq volcano plot settings). These configurations define default values, expected columns, thresholds, colors, legends, and more.

- **shared/**:  
  Contains configurations that apply across multiple domains. This is useful for common defaults and parameters that should remain consistent throughout the platform.

**Usage:**  
The backend application utilizes the configuration files by loading them through utility functions (such as those in `backend/app/utils/config_loader.py`). These configurations are parsed at runtime and can be converted to JSON when being served via API endpoints.

**Maintenance:**  
- Ensure that each configuration file is documented, with comments included at the top of each YAML file to explain its purpose.  
- Update this README if new folders or structure changes are introduced.
