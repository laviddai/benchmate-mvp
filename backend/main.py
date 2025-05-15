from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import importlib
import pkgutil
from pathlib import Path

app = FastAPI(title="BenchMate Backend API")

# Enable CORS so the frontend at localhost:3000 can communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # adjust in production as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def include_routers_from_package(app: FastAPI, package_name: str, api_prefix: str = "/api"):
    """
    Dynamically import all modules under the given package and include any
    FastAPI routers they expose. Routers are expected to be named 'router'.
    The URL prefix is constructed as api_prefix + '/' + path segments of the module.
    e.g., module 'app.endpoints.benchtop.biology.volcano' => '/api/benchtop/biology/volcano'
    """
    package = importlib.import_module(package_name)
    package_path = Path(package.__file__).parent

    for finder, module_name, ispkg in pkgutil.walk_packages([str(package_path)], package_name + "."):
        module = importlib.import_module(module_name)
        if hasattr(module, "router"):
            # derive URL path by stripping the base package and the module name
            rel_path = module_name[len(package_name) + 1:]
            parts = rel_path.split('.')
            prefix = api_prefix + '/' + '/'.join(parts[:-1])  # exclude the module file name
            app.include_router(module.router, prefix=prefix, tags=[parts[-1]])

# Automatically include all routers defined under app.endpoints
include_routers_from_package(app, "app.endpoints")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
