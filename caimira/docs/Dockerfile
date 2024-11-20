# Use the conda image to install Python
FROM registry.cern.ch/docker.io/condaforge/mambaforge AS conda

ARG PYTHON_VERSION=3.12
RUN mamba create --yes -p /opt/app python=${PYTHON_VERSION}

# Install system dependencies, including Graphviz
RUN conda install conda-forge::graphviz

# Copy project files to the container
COPY . /app
WORKDIR /app

# Install CAiMIRA docs
RUN pip install .[doc]

# Sphinx directory
WORKDIR /app/docs/sphinx

# Generate markdown project's documentation
RUN sphinx-build -b markdown . _build/markdown

# Base docs directory
WORKDIR /app/docs

# Run the Python script to update markdown files, move it, and generate UML diagram
RUN python3 style_docs.py \
&& mv sphinx/_build/markdown/index.md mkdocs/docs/code/models.md \
&& pyreverse -o png -p UML-CAiMIRA --output-directory mkdocs/docs/code ../src/caimira/calculator/models/models.py

# Mkdocs directory
WORKDIR /app/docs/mkdocs

# Command to serve the MkDocs site
CMD ["python", "-m", "mkdocs", "serve", "--dev-addr=0.0.0.0:8080"]
