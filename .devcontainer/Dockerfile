######################################################################
#  Base image: Python 3.12 + Node LTS (provided by the Dev Containers
#  team).  We extend it so that:
#    • Java 17 is available for ImageJ/Fiji (future task)
#    • Any additional OS libraries can be added in one place
######################################################################
FROM mcr.microsoft.com/devcontainers/python:3.12-node

# ---- System packages ------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       openjdk-17-jdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---- Default shell --------------------------------------------------
CMD ["bash"]
