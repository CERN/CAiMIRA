## Docker

The easiest way to run a version of CAiMIRA Calculator is to use docker. 
Install Docker software here: [https://www.docker.com/](https://www.docker.com/)

### Using the pre-built image

1. Load a pre-built image of CAiMIRA, available at [https://gitlab.cern.ch/caimira/caimira/container_registry](https://gitlab.cern.ch/caimira/caimira/container_registry).
In order to run CAiMIRA locally with docker, run the following:

    docker run -it -p 8080:8080 -e APP_NAME='calculator-app' gitlab-registry.cern.ch/caimira/caimira/calculator-app

2. This will start a local version of CAiMIRA, which can be visited by loading this URL in your browser: [http://localhost:8080/](http://localhost:8080/)

### Building the full environment

To build the full environment (_i.e. ...?? Luis, what does full environment mean?_) for local development, from the root directory of the project, run:

```
docker build -f app-config/api-app/Dockerfile -t api-app .
docker build -f app-config/calculator-app/Dockerfile -t calculator-app .
docker build ./app-config/auth-service -t auth-service
```

If you are using a computer with ARM CPU (Mac M1/2/3), then add the arg `--platform linux/arm64` to the 3 `docker build` cmds.

If you need to debug the Docker build, add the args `--no-cache --progress=plain` to the 3 `docker build` cmds (??) to see a more verbose output in your terminal.

Get the client secret from the CERN Application portal for the `caimira-test` app. See [CERN-SSO-integration](deployment.md#cern-sso-integration) for more info.
```
read CLIENT_SECRET
```

Define some env vars (copy/paste):
```
export COOKIE_SECRET=$(openssl rand -hex 50)
export OIDC_SERVER=https://auth.cern.ch/auth
export OIDC_REALM=CERN
export CLIENT_ID=caimira-test
export CLIENT_SECRET=$CLIENT_SECRET
```

Run docker compose in the root folder:
```
cd app-config
CURRENT_UID=$(id -u):$(id -g) docker compose up
```

Then visit [http://localhost:8080/](http://localhost:8080/).

## Development mode

To install the code locally in development mode clone the repository from Gitlab:
1. Go to [https://gitlab.cern.ch/caimira/caimira/](https://gitlab.cern.ch/caimira/caimira/)
2. Code → Clone with HTTPS
3. Choose a root folder for the project

CAiMIRA is also mirrored to Github if you wish to collaborate on development: [https://github.com/CERN/caimira](https://github.com/CERN/caimira)

### Source code folder structure

The project contains two different Python packages:

- `caimira`: Contains all the backend logic and the generic calculator UI. This package is published in [PyPI](https://pypi.org/project/caimira/).
- `cern_caimira`: Imports and uses the backend package (`caimira`) and includes CERN-specific UI features.

The folder layout follows best practices as described [here](https://ianhopkinson.org.uk/2022/02/understanding-setup-py-setup-cfg-and-pyproject-toml-in-python/).

### Setup

Installing CAiMIRA in editable mode and running the Calculator app:

#### Installing

In order to install the CAiMIRA's backend logic, create your own `virtualenv` and, from the root directory of the project, run:

```
cd caimira
pip install -e .
```

In order to install the CERN-specific UI version, that links to the previously installed backend, activate your `virtualenv` and, from the root directory of the project, run:

```
cd cern_caimira
pip install -e .
```

#### Running

This example describes how to run the calculator with the CERN-specific UI. In the root directory of the project:

```
python -m cern_caimira.apps.calculator
```

To run with a specific template theme created:

```
python -m cern_caimira.apps.calculator --theme=cern_caimira/src/cern_caimira/apps/templates/{theme}
```

To run the entire app in a different `APPLICATION_ROOT` path:

```
python -m cern_caimira.apps.calculator --app_root=/myroot
```

To run the calculator on a different URL path:

```
python -m cern_caimira.apps.calculator --prefix=/mycalc
```

Each of these commands will start a local version of CAiMIRA, which can be visited at [http://localhost:8080/](http://localhost:8080/).

#### REST API

To use the REST API, from the root directory of the project:

1. Run the backend API:

    ```
    python -m caimira.api.app
    ```

2. The Tornado server will run on port `8081`.

To test the API functionality, you can send a `POST` request to `http://localhost:8081/virus_report` with the required inputs in the request body. For an example of the required inputs, see [the baseline raw form data](https://gitlab.cern.ch/caimira/caimira/blob/master/caimira/src/caimira/calculator/validators/virus/virus_validator.py#L565).

The response format will be:

```json
{
    "status": "success",
    "message": "Results generated successfully",
    "report_data": {
        ...
    },
    ...
}
```

For further details please refer to the [REST API documentation page](../code/rest_api.md).

#### Running the Expert-Apps
 
The CAiMIRA Expert App and the CO2 App are tools to dynamically interact with various parameters of the CAiMIRA model. 

##### Note

The `ExpertApplication` and `CO2Application` are no longer actively maintained but will remain in the codebase for legacy purposes.
Please note that the functionality of these applications might be compromised due to deprecation issues.

##### Running the Applications

These applications only work within Jupyter notebooks. Attempting to run them outside of a Jupyter environment may result in errors or degraded functionality.

Make sure you have the needed dependencies installed:

```
pip install notebook jupyterlab
```

Running with Visual Studio Code (VSCode):

1. Ensure you have the following extensions installed in VSCode: `Jupyter` and `Python`.

2. Open VSCode and navigate to the directory containing the notebook.

3. Open the notebook (e.g. `caimira/apps/expert/caimira.ipynb`) and run the cells by clicking the `run` button next to each cell.


### Installing and running tests

The project contains test files that separately test the functionality of the `caimira` backend and `cern_caimira` UI.

To test the `caimira` package, from the root repository of the project:

```
cd caimira
pip install -e .[test]
python -m pytest
```

To test the `cern_caimira` package, from the root repository of the project:

```
cd cern_caimira
pip install -e .[test]
python -m pytest
```

### Running the profiler

CAiMIRA includes a profiler designed to identify performance bottlenecks. The profiler is enabled when the environment variable `CAIMIRA_PROFILER_ENABLED` is set to 1.

When visiting [http://localhost:8080/profiler](http://localhost:8080/profiler), you can start a new session and choose between [PyInstrument](https://github.com/joerick/pyinstrument) or [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile). The app includes two different profilers, mainly because they can give different information.

Keep the profiler page open. Then, in another window, navigate to any page in CAiMIRA, for example generate a new report. Refresh the profiler page, and click on the `Report` link to see the profiler output.

The sessions are stored in a local file in the `/tmp` folder. To share it across multiple web nodes, a shared storage should be added to all web nodes. The folder can be customized via the environment variable `CAIMIRA_PROFILER_CACHE_DIR`.

### Compiling and viewing the docs

To compile and view CAiMIRA's documentation, follow these steps:

1. Install CAiMIRA with Documentation Dependencies

    First, ensure CAiMIRA is installed along with the `doc` dependencies:

        cd caimira
        pip install -e .[doc]

2. Generate Code Documentation in Markdown

    Use `sphinx` with `sphinx_markdown_builder` to generate the documentation in `Markdown` format:

        cd docs/sphinx
        sphinx-build -b markdown . _build/markdown

3. Customize and Organize Documentation

    Run the `style_docs.py` script to apply custom styles, move required files, and generate a UML diagram:

        python style_docs.py \
        && mv sphinx/_build/markdown/index.md mkdocs/docs/code/models.md \
        && pyreverse -o png -p UML-CAiMIRA --output-directory mkdocs/docs ../src/caimira/calculator/models/models.py

4. Start the documentation server

    To view the documentation locally, use MkDocs to serve it:
 
        cd ../mkdocs
        python -m mkdocs serve --dev-addr=0.0.0.0:8080

    The documentation can now be accessed at [http://0.0.0.0:8080/](http://0.0.0.0:8080/).
