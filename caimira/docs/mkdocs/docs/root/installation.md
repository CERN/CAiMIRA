This installation guide provides instructions for both quickly running CAiMIRA with the Calculator App using a pre-built Docker image, as well as instructions on how to set up a development environment for advanced use cases. It is therefore structured to accommodate a variety of users, from those seeking a simple, quick-start solution, to developers requiring a detailed setup for customization and development.

**Guide Overview**:

1. **[Quick Start](#quick-start)**: Designed for users aiming to run CAiMIRA with minimal setup. The Quick Guide section outlines the fastest approach to using CAiMIRA through a pre-built Docker image.
2. **[Development Installation](#development-installation)**: Intended for developers or those requiring advanced customization. This section includes detailed steps for setting up the environment, customizing the UI, running the backend REST API, and contributing to the project.

## Quick Start

The easiest way to run a version of CAiMIRA with its Calculator App is to use Docker. A pre-built image of CAiMIRA is made available at [this](https://gitlab.cern.ch/caimira/caimira/container_registry) GitLab container registry.

### Prerequisites

Before proceeding, ensure the following prerequisites are met:

1. **Docker Installed**:

    Install Docker on the system. Instructions for installation can be found at [Docker's official website](https://www.docker.com/products/docker-desktop/).

    Verify the installation by opening a terminal and running:

        docker --version

2. **Network Access**:

    Ensure the machine has internet access to pull the CAiMIRA image from the container registry.

### Running the pre-built Image

In order to run CAiMIRA locally with Docker, run the following instruction in a terminal:

    docker run -it -p 8080:8080 -e APP_NAME='calculator-app' gitlab-registry.cern.ch/caimira/caimira/calculator-app

This will start a local version of CAiMIRA, which can be visited by loading this URL in your browser [http://localhost:8080/](http://localhost:8080/).

## Development Installation

This section provides comprehensive instructions for setting up the CAiMIRA environment in development mode. The guide is tailored for contributors and advanced users who want to build the project from source, customize its features, or contribute to its codebase<sup>1</sup>.

Developers can follow the steps below to build and run the CAiMIRA backend, APIs, or Calculator applications, run tests, and generate the documentation. Additionally, this section includes instructions for running legacy expert applications, profiling the system, and testing specific features.

The project contains two different Python packages:

- `caimira`: Contains the backend logic and the APIs logic. This package is published in [PyPI](https://pypi.org/project/caimira/).
- `cern_caimira`: Imports and uses the backend package (`caimira`) and includes the CAiMIRA-native UI features.

The folder layout follows best practices as described [here](https://ianhopkinson.org.uk/2022/02/understanding-setup-py-setup-cfg-and-pyproject-toml-in-python/).

!!! info
    <sup>1</sup> The project's main repository is hosted on [GitLab](https://gitlab.cern.ch/caimira/caimira). Even though the repository is public, contributions to GitLab are restricted to users with a valid CERN SSO. 
    
    For external contributions and collaboration, a mirror is maintained on [GitHub](https://github.com/CERN/caimira). 

### Prerequisites

Before proceeding with the development installation of CAiMIRA, ensure that your system meets the following prerequisites:

1. **Python Environment**:

    - Python `3.9` or later.
    - `pip`, `setuptools` must but installed and up-to-date. You can update them by opening a terminal and running:

            python -m pip install --upgrade pip setuptools

        !!! note
            It's recommended to use `pyenv` or similar tools to manage Python versions. For  details on how to install and use `pyenv`, see [here](https://github.com/pyenv/pyenv). While not mandatory, it is also recommended to create a virtual environment (`virtualenv`) to avoid conflicts between different package versions. For more information on setting up a virtual environment, see [here](https://virtualenv.pypa.io/en/latest/).

2. **Git**:

    - Ensure that Git is installed for cloning the repository. You can download it [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git). Verify installation by opening a terminal and running:

            git --version

3. **Docker**:

    - While not strictly required for local development, Docker is useful for creating isolated environments and running CAiMIRA in production-like settings. Further details can be found in the [Setting up full environment](#setting-up-the-full-environment) section.

4. **Development Tools**:

    - A code editor such as [VSCode](https://code.visualstudio.com/), or an IDE like [PyCharm](https://www.jetbrains.com/pycharm/).

### Installing and running

This section provides instructions for setting up, running, and testing CAiMIRA in a local development environment. 

Cloning the full repository from GitLab is required for using the [native Calculator app](#calculator), running [tests](#tests), [profiling](#profiler), or generating [documentation](#docs). 

**For development and/or running the backend model alone (without a UI), or for REST API integration, go directly to the [Backend](#backend) section.**

The repository can be cloned with the following command:

!!! note
    The directory in which you run these commands will be the root directory of your project.

```
git clone https://gitlab.cern.ch/caimira/caimira.git  
```

This ensures access to both the backend and the native UI, along with all tools and resources.

#### Calculator

The following sections provide step-by-step instructions for setting up and running the native CAiMIRA Calculator app and associated applications in a local development environment. It is designed for users seeking to develop new features, test existing functionalities, or explore the available tools.

!!! info
    The CAiMIRA Calculator integrates the backend functionality with a CAiMIRA-native UI, offering a complete webpage for modeling and interaction. Therefore, local installation of the two packages - [`caimira`](#installing-backend) and [`cern_caimira`](#installing-ui) - in editable mode is required, and are described in the following sections.

##### Installing backend

In order to install the CAiMIRA backend, from the root directory of the project, run:

    cd caimira
    pip install -e .

##### Installing UI:

In order to install the CAiMIRA-native UI, that links to the previously installed backend, from the root directory of the project, run:

    cd cern_caimira
    pip install -e .

##### Running:

The calculator can be started with the CAiMIRA-native UI using the following command (directory independent):

    python -m cern_caimira.apps.calculator

Additional options allow customization, such as specifying themes, application roots, or URL paths. For example:

- **Run with a specific template theme**:

    Within a given UI framework, you can choose different "themes" changing some frontend logic, style and text. To run with a specific template theme created:

        python -m cern_caimira.apps.calculator --theme=cern_caimira/src/cern_caimira/apps/templates/{theme}

    Where `{theme}` is the name of the folder within the `cern_caimira/apps/templates/` directory. E.g. for the `cern` theme:

        python -m cern_caimira.apps.calculator --theme=cern_caimira/src/cern_caimira/apps/templates/cern

- **Run the app with a different `APPLICATION_ROOT` path**:

    The base path of the web application on the server. It determines where the app is "rooted" in relation to the server's URL structure. To run with a specific application root:

        python -m cern_caimira.apps.calculator --app_root=/myroot

- **Run the Calculator App on a different `CAIMIRA_CALCULATOR_PREFIX` URL path**:

    The base path of the CAiMIRA calculator. It determines the URL path within the Calculator App itself. To run with a specific prefix:

        python -m cern_caimira.apps.calculator --prefix=/mycalc

Each of these commands will start a local version of CAiMIRA, which can be visited at [http://localhost:8080/](http://localhost:8080/).

##### Expert-Apps:

The CAiMIRA Expert App and CO<sub>2</sub> App are legacy tools designed to provide dynamic interaction with the CAiMIRA model parameters.

!!! warning

    The `ExpertApplication` and `CO2Application` are no longer actively maintained but will remain in the codebase for legacy purposes.
    Please note that the functionality of these applications might be compromised due to deprecation issues.

These apps only work within Jupyter notebooks. 

!!! warning
    
    Attempting to run them outside of a Jupyter environment may result in errors or degraded functionality.

1. **Install dependencies**:

    Install Jupyter Notebook and JupyterLab to use the applications:

        pip install notebook jupyterlab

2. **Run with Visual Studio Code**:

    - Ensure you have the following extensions installed in VSCode: `Jupyter` and `Python`.

    - Open VSCode and navigate to the directory containing the notebook.

    - Open the notebook (e.g. `caimira/apps/expert/caimira.ipynb`) and run the cells by clicking the `run` button next to each cell.

#### Tests

CAiMIRA includes a suite of tests to validate the functionality of both its backend (`caimira` package) and UI components (`cern_caimira` package).

1. **Testing the backend (`caimira` package)**:

    Install test dependencies and run the tests. From the root directory run:

        cd caimira
        pip install -e .[test]
        python -m pytest

2. **Testing the UI (`cern_caimira` package)**:

    Install test dependencies and run the tests. From the root directory run:
    
        cd cern_caimira
        pip install -e .[test]
        python -m pytest

#### Profiler

CAiMIRA includes a profiler designed to identify performance bottlenecks. The profiler is enabled when the environment variable `CAIMIRA_PROFILER_ENABLED` is set to 1.

When visiting [http://localhost:8080/profiler](http://localhost:8080/profiler), you can start a new session and choose between [PyInstrument](https://github.com/joerick/pyinstrument) or [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile). The app includes two different profilers, mainly because they can give different information.

Keep the profiler page open. Then, in another window, navigate to any page in CAiMIRA, for example generate a new report. Refresh the profiler page, and click on the `Report` link to see the profiler output.

The sessions are stored in a local file in the `/tmp` folder. To share it across multiple web nodes, a shared storage should be added to all web nodes. The folder can be customized via the environment variable `CAIMIRA_PROFILER_CACHE_DIR`.

#### Docs

CAiMIRA includes comprehensive documentation, which can be compiled and viewed locally:

1. **Install CAiMIRA with documentation dependencies**:

    First, ensure CAiMIRA is installed along with the `doc` dependencies:

        cd caimira
        pip install -e .[doc]

2. **Generate code documentation in markdown**:

    Use `sphinx` with `sphinx_markdown_builder` to generate the documentation in `Markdown` format:

        cd docs/sphinx
        sphinx-build -b markdown . _build/markdown

3. **Customize and organize documentation**:

    Run the `style_docs.py` script to apply custom styles, move required files, and generate a UML diagram:

        python style_docs.py \
        && mv sphinx/_build/markdown/index.md mkdocs/docs/code/models.md \
        && pyreverse -o png -p UML-CAiMIRA --output-directory mkdocs/docs ../src/caimira/calculator/models/models.py

4. **Start the documentation server**:

    To view the documentation locally, use MkDocs to serve it:
 
        cd ../mkdocs
        python -m mkdocs serve --dev-addr=0.0.0.0:8080

    The documentation can now be accessed at [http://0.0.0.0:8080/](http://0.0.0.0:8080/).

#### Backend

The CAiMIRA backend includes the logic underlying the [physics model](https://caimira-test.docs.cern.ch/root/physics_model/) and the REST API for programmatic interaction with the models. Local installation enables full access to these features, supporting development and testing.

##### Installing

CAiMIRA's backend logic can be installed with the following two options:

1. **From [PyPI](https://pypi.org/project/caimira/)**:

        pip install caimira
            
2. **From the [GitLab Repository](https://gitlab.cern.ch/caimira/caimira)<sup>1</sup>**:
    
    Clone the repository and install it in editable mode for development by running the following commands:

        git clone https://gitlab.cern.ch/caimira/caimira.git
        cd caimira
    
    In the root directory:
        
        cd caimira
        pip install -e .

    !!! note
        <sup>1</sup>In case you haven't cloned the repository before.

##### Running and testing with API

CAiMIRA backend includes a REST API for programmatic interaction with its models. The following steps describe how to run and test the API locally.
    
1. **Run the backend API**:
    
        python -m caimira.api.app

    The Tornado server will be accessible at [http://localhost:8081/](http://localhost:8081/).

2. **Test the API**:

    Send a `POST` request to  `http://localhost:8081/virus/report` with the required inputs in the body. Example request formats can be found in the [Virus Validator Code](https://gitlab.cern.ch/caimira/caimira/blob/master/caimira/src/caimira/calculator/validators/virus/virus_validator.py#L565).

3. **Example Response**:
    A successful response will return data in the following format:

    !!! success
            {
                "status": "success",
                "message": "Results generated successfully",
                "results": {
                    ...
                },
                ...
            }
    
    For further details please refer to the [REST API documentation page](../code/rest_api.md).

### Setting up the full environment

This section outlines the steps to build and run the full CAiMIRA environment locally using Docker. It provides instructions for creating the necessary Docker images, configuring authentication, and running the application with Docker Compose. 

#### Prerequisites

After following what is described in the main [prerequisites](#prerequisites) section, ensure the following tools are installed and properly configured:

1. **CAiMIRA repository**: Can be cloned from the official GitLab repository [here](https://gitlab.cern.ch/caimira/caimira).
2. **Docker**: Download from the [Docker's official website](https://www.docker.com/products/docker-desktop/).
3. **Docker Compose**: Instructions on [DockerDocks official page](https://docs.docker.com/compose/install/).

#### Build and run

To build and run the environment, the following steps can be performed from the root directory of the project:

1. **Build Docker Images**:

    To build the full environment for local development, from the root directory of the project, run:

        docker build -f app-config/api-app/Dockerfile -t api-app .
        docker build -f app-config/calculator-app/Dockerfile -t calculator-app .
        docker build ./app-config/auth-service -t auth-service

    For systems with ARM CPUs (e.g. Mac M1/M2/M3), the argument `--platform linux/arm64` should be appended to each `docker build` command.
    For more verbose output during the Docker build process, additional arguments `no-cache --progress=plain` can be include to each command.

2. **Obtain the Client Secret**:

    The client secret for the `caimira-test` application must be retrieved from the CERN Application Portal. Further details can be found in the[CERN-SSO-integration](deployment.md#cern-sso-integration) documentation.

        read CLIENT_SECRET

3. **Set Environment Variables**:

    Required environment variables can be defined as follows (copy/paste):

        export COOKIE_SECRET=$(openssl rand -hex 50)
        export OIDC_SERVER=https://auth.cern.ch/auth
        export OIDC_REALM=CERN
        export CLIENT_ID=caimira-test
        export CLIENT_SECRET=$CLIENT_SECRET
        
4. **Run the Application**:

    Start the application using Docker Compose running in the root directory:
    
        cd app-config
        CURRENT_UID=$(id -u):$(id -g) docker compose up

    Then visit [http://localhost:8080/](http://localhost:8080/).
