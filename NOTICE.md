# Third-Party Attributions

BenchMate bundles the following open-source software, all under permissive licenses that allow commercial use:

## Runtime

| Component  | Version | License      | URL                                     |
|------------|---------|--------------|-----------------------------------------|
| Python     | 3.12    | PSF          | https://www.python.org/                 |
| Node.js    | 18.x LTS| MIT          | https://nodejs.org/                     |
| Docker     | latest  | Apache 2.0   | https://www.docker.com/                 |

## Frontend (JavaScript ecosystem)

| Package            | Version   | License | URL                                                         |
|--------------------|-----------|---------|-------------------------------------------------------------|
| React              | 18.2.0    | MIT     | https://github.com/facebook/react                          :contentReference[oaicite:1]{index=1} |
| react-dom          | 18.2.0    | MIT     | https://github.com/facebook/react                          :contentReference[oaicite:3]{index=3} |
| react-router-dom   | 6.14.1    | MIT     | https://github.com/remix-run/react-router-dom               :contentReference[oaicite:5]{index=5} |
| react-scripts      | 5.0.1     | MIT     | https://github.com/facebook/create-react-app                :contentReference[oaicite:7]{index=7} |
| cross-env          | 7.0.3     | MIT     | https://github.com/kentcdodds/cross-env                     :contentReference[oaicite:9]{index=9} |
| Tailwind CSS       | 3.x.x     | MIT     | https://github.com/tailwindlabs/tailwindcss                |

## Backend (Python ecosystem)

| Package    | Version    | License  | URL                                                        |
|------------|------------|----------|------------------------------------------------------------|
| FastAPI    | 0.101.0    | MIT      | https://github.com/tiangolo/fastapi                        |
| Uvicorn    | 0.24.0     | BSD 3-Clause | https://github.com/encode/uvicorn                          |
| PyYAML     | 6.0        | MIT      | https://github.com/yaml/pyyaml                             |
| pandas     | 2.0.3      | BSD 3-Clause | https://github.com/pandas-dev/pandas                        |
| numpy      | 1.25.0     | BSD 3-Clause | https://github.com/numpy/numpy                              |
| matplotlib | 3.8.0      | PSF      | https://github.com/matplotlib/matplotlib                   |
| scikit-learn | latest   | BSD 3-Clause | https://github.com/scikit-learn/scikit-learn               |
| scanpy     | latest     | MIT      | https://github.com/theislab/scanpy                          |
| **…**      | **…**      | **…**    | For full list, see [`backend/requirements_biology.txt`]    :contentReference[oaicite:11]{index=11} |

## Imaging

| Tool       | Version  | License    | URL                                                          |
|------------|----------|------------|--------------------------------------------------------------|
| Fiji (ImageJ) | latest | GPL 3.0    | https://github.com/fiji/fiji                                 :contentReference[oaicite:12]{index=12} |
| ImageJ2 core  | 2.x.x  | BSD 2-Clause | https://imagej.net/ImageJ2                                   |

---

> **Notes**  
> - All listed software permits commercial use.  
> - Where a package has many sub-components (e.g., Fiji), refer to its main license.  
> - For the complete set of Python dependencies (and their exact versions), see `backend/requirements_biology.txt`.  
> - If you add new third-party packages, please update this `NOTICE.md`.

