######################################################################
#  BenchMate backend image (FastAPI + bio libs)
#  • Based on the slim Python 3.12 image to keep size down
#  • Installs system libs needed by core scientific packages
#  • Copies the backend code into /app and sets uvicorn as entrypoint
######################################################################
FROM python:3.12-slim

# -- System dependencies (minimal set for now) -----------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libgomp1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# -- Python dependencies ---------------------------------------------
COPY backend/requirements_biology.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# -- Project source ---------------------------------------------------
WORKDIR /app
COPY backend/ /app

# -- Default command --------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
