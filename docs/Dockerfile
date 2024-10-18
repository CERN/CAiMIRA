# Use the base mambaforge image from CERN's Docker registry
FROM registry.cern.ch/docker.io/condaforge/mambaforge

# Use argument for Python version
ARG PYTHON_VERSION=3.12

# Create a conda environment with the desired Python version
RUN mamba create --yes -n mkdocs-env python=${PYTHON_VERSION} \
    && conda clean --all --yes

# Copy project files to the container
COPY . /app
WORKDIR /app

# Install MkDocs and dependencies using pip or conda
RUN mamba run -n mkdocs-env pip install -r requirements.txt

# Expose port 8000 to serve MkDocs
EXPOSE 8000

# Command to serve the MkDocs site
CMD ["mamba", "run", "-n", "mkdocs-env", "mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
