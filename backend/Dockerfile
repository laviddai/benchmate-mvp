######################################################################
#  BenchMate backend image (FastAPI + bio libs)
#  • Context root is the backend/ folder
#  • Installs minimal system libs for Python scientific packages
#  • Copies requirements and code from the current context into /app
######################################################################
FROM python:3.12-slim

# --- System dependencies --------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libgomp1 \
       openjdk-17-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- Python dependencies --------------------------------------------
# Context root contains requirements_biology.txt directly
COPY requirements_biology.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# --- Application code -----------------------------------------------
WORKDIR /app
# Copy everything from the backend/ folder into /app
COPY . /app

# --- Default startup command ----------------------------------------
# main.py must expose FastAPI app as 'app'
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
