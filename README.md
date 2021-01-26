# CARA - COVID Airborne Risk Assessment

## Applications

### COVID Calculator

A risk assessment tool which simulates the long range airborne spread of the
SARS-CoV-2 virus for space managers.

You can find the CARA COVID Calculator at https://cara.web.cern.ch/calculator/.
Please see the [COVID Calculator README for detailed usage instructions](cara/apps/calculator/README.md).

### CARA Expert App

A tool to interact with various parameters of the CARA model.
This is currently in beta, and can be found at https://cara.web.cern.ch/expert-app.


## Development guide

### Running the COVID calculator app locally

```
pip install -e .   # At the root of the repository
python -m cara.apps.calculator
```

### Running the CARA Expert-App app locally

```
pip install -e .   # At the root of the repository
voila ./app/cara.ipynb
```


Then visit http://localhost:8080/calculator.


### Running the tests

```
pip install -e .[test]
pytest ./cara
```

### Building the whole environment for local execution

**Simulate the docker build that takes place on openshift with:**

```
s2i build file://$(pwd) --copy --keep-symlinks --context-dir ./app-config/nginx/ centos/nginx-112-centos7 cara-nginx-app
s2i build file://$(pwd) --copy --keep-symlinks --env APP_NAME=cara-voila --context-dir ./ centos/python-36-centos7 cara-voila-app
s2i build file://$(pwd) --copy --keep-symlinks --env APP_NAME=cara-webservice --context-dir ./  centos/python-36-centos7 cara-webservice
cd app-config
docker-compose up
```

Then visit http://localhost:8080/.

### Setting up the application on openshift

The https://cern.ch/cara application is running on CERN's OpenShift platform. In order to set it up for the first time, we followed the documentation at https://cern.service-now.com/service-portal?id=kb_article&n=KB0004498. In particular we:

 * Added the OpenShift application deploy key to the GitLab repository
 * Created a Python 3.6 (the highest possible at the time of writing) application in OpenShift
 * Configured a generic webhook on OpenShift, and call that from the CI of the GitLab repository

### Updating the test-cara.web.cern.ch instance

We have a replica of https://cara.web.cern.ch running on http://test-cara.web.cern.ch. Its purpose is to simulate what will happen when
a feature is merged. To push your changes to test-cara, simply push your branch to `live/test-cara` and the CI pipeline will trigger the
deployment. To push to this branch, there is a good chance that you will need to force push - you should always force push with care and
understanding why you are doing it. Syntactically, it will looks something like (assuming that you have "upstream" as your remote name,
but it may be origin if you haven't configured it differently):

    git push --force upstream name-of-local-branch:live/test-cara



