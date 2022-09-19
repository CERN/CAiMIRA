# CAiMIRA - CERN Airborne Model for Risk Assessment

CAiMIRA is a risk assessment tool developed to model the concentration of viruses in enclosed spaces, in order to inform space-management decisions.

CAiMIRA models the concentration profile of potential virions in enclosed spaces , both as background (room) concentration and during close-proximity interations, with clear and intuitive graphs.
The user can set a number of parameters, including room volume, exposure time, activity type, mask-wearing and ventilation.
The report generated indicates how to avoid exceeding critical concentrations and chains of airborne transmission in spaces such as individual offices, meeting rooms and labs.

The risk assessment tool simulates the airborne spread SARS-CoV-2 virus in a finite volume, assuming a homogenous mixture and a two-stage exhaled jet model, and estimates the risk of COVID-19 infection therein.
The results DO NOT include the other known modes of SARS-CoV-2 transmission, such as fomite or blood-bound.
Hence, the output from this model is only valid when the other recommended public health & safety instructions are observed, such as good hand hygiene and other barrier measures.

The model used is based on scientific publications relating to airborne transmission of infectious diseases, dose-response exposures and aerosol science, as of February 2022.
It can be used to compare the effectiveness of different airborne-related risk mitigation measures.

Note that this model applies a deterministic approach, i.e., it is assumed at least one person is infected and shedding viruses into the simulated volume.
Nonetheless, it is also important to understand that the absolute risk of infection is uncertain, as it will depend on the probability that someone infected attends the event.
The model is most useful for comparing the impact and effectiveness of different mitigation measures such as ventilation, filtration, exposure time, physical activity, amount and nature of close-range interactions and
the size of the room, considering both long- and short-range airborne transmission modes of COVID-19 in indoor settings.

This tool is designed to be informative, allowing the user to adapt different settings and model the relative impact on the estimated infection probabilities.
The objective is to facilitate targeted decision-making and investment through comparisons, rather than a singular determination of absolute risk.
While the SARS-CoV-2 virus is in circulation among the population, the notion of 'zero risk' or 'completely safe scenario' does not exist.
Each event modelled is unique, and the results generated therein are only as accurate as the inputs and assumptions.

## Authors
CAiMIRA was developed by following members of CERN - European Council for Nuclear Research (visit https://home.cern/):

Andre Henriques<sup>1</sup>, Luis Aleixo<sup>1</sup>, Marco Andreini<sup>1</sup>, Gabriella Azzopardi<sup>2</sup>, James Devine<sup>3</sup>, Philip Elson<sup>4</sup>, Nicolas Mounet<sup>2</sup>, Markus Kongstein Rognlien<sup>2,6</sup>, Nicola Tarocco<sup>5</sup>

<sup>1</sup>HSE Unit, Occupational Health & Safety Group, CERN<br>
<sup>2</sup>Beams Department, Accelerators and Beam Physics Group, CERN<br>
<sup>3</sup>Experimental Physics Department, Safety Office, CERN<br>
<sup>4</sup>Beams Department, Controls Group, CERN<br>
<sup>5</sup>Information Technology Department, Collaboration, Devices & Applications Group, CERN<br>
<sup>6</sup>Norwegian University of Science and Technology (NTNU)<br>

### Reference and Citation

**For the use of the CAiMIRA web app**

CAiMIRA – CERN Airborne Model for Indoor Risk Assessment tool

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6520432.svg)](https://doi.org/10.5281/zenodo.6520432)

© Copyright 2020-2021 CERN. All rights not expressly granted are reserved.

**For use of the CAiMIRA model**

Henriques A, Mounet N, Aleixo L, Elson P, Devine J, Azzopardi G, Andreini M, Rognlien M, Tarocco N, Tang J. (2022). Modelling airborne transmission of SARS-CoV-2 using CARA: risk assessment for enclosed spaces. _Interface Focus 20210076_. https://doi.org/10.1098/rsfs.2021.0076

Reference on the Short-range expiratory jet model from:
Jia W, Wei J, Cheng P, Wang Q, Li Y. (2022). Exposure and respiratory infection risk via the short-range airborne route. _Building and Environment_ *219*: 109166. 
https://doi.org/10.1016/j.buildenv.2022.109166

## Applications

### Calculator

A risk assessment tool which simulates the airborne spread of the SARS-CoV-2 virus for space managers.


### CAiMIRA Expert App

A tool to interact with various parameters of the CAiMIRA model.


## Disclaimer

CAiMIRA has not undergone review, approval or certification by competent authorities, and as a result, it cannot be considered as a fully endorsed and reliable tool, namely in the assessment of potential viral emissions from infected hosts to be modelled.

The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and non-infringement.
In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.


## Running CAiMIRA locally

The easiest way to run a version of CAiMIRA Calculator is to use docker. A pre-built
image of CAiMIRA is made available at https://gitlab.cern.ch/cara/caimira/container_registry.
In order to run CAiMIRA locally with docker, run the following:

    $ docker run -it -p 8080:8080 gitlab-registry.cern.ch/cara/caimira/calculator

This will start a local version of CAiMIRA, which can be visited at http://localhost:8080/.


## Development guide

CAiMIRA is also mirrored to Github if you wish to collaborate on development and can be found at: https://github.com/CERN/caimira

### Installing CAiMIRA in editable mode

```
pip install -e .   # At the root of the repository
```

### Running the Calculator app in development mode

```
python -m caimira.apps.calculator
```

To run with the CERN theme:

```
python -m caimira.apps.calculator --theme=caimira/apps/templates/cern
```

To run the calculator on a different URL path:

```
python -m caimira.apps.calculator --prefix=/mycalc
```

### How to compile and read the documentation

In order to generate the documentation, CAiMIRA must be installed first with the `doc` dependencies:

```
pip install -e .[doc]
```

To generate the HTML documentation page, the command `make html` should be executed in the `caimira/docs` directory. 
If any of the `.rst` files under the `caimira/docs` folder is changed, this command should be executed again.

Then, right click on `caimira/docs/_build/html/index.html` and select `Open with` your preferred web browser.

### Running the CAiMIRA Expert-App app in development mode

```
voila caimira/apps/expert/caimira.ipynb --port=8080
```

Then visit http://localhost:8080.


### Running the tests

```
pip install -e .[test]
pytest ./caimira
```

### Building the whole environment for local development

**Simulate the docker build that takes place on openshift with:**

```
s2i build file://$(pwd) --copy --keep-symlinks --context-dir ./app-config/nginx/ centos/nginx-112-centos7 caimira-nginx-app
docker build . -f ./app-config/caimira-webservice/Dockerfile -t caimira-webservice
docker build ./app-config/auth-service -t auth-service
```

Get the client secret from the CERN Application portal for the `caimira-test` app. See [CERN-SSO-integration](#CERN-SSO-integration) for more info.
```
read CLIENT_SECRET
```

Define some env vars (copy/paste):
```
export COOKIE_SECRET=$(openssl rand -hex 50)
export OIDC_SERVER=https://auth.cern.ch/auth
export OIDC_REALM=CERN
export CLIENT_ID=caimira-test
export CLIENT_SECRET
```

Run docker-compose:
```
cd app-config
CURRENT_UID=$(id -u):$(id -g) docker-compose up
```

Then visit http://localhost:8080/.

### Setting up the application on openshift

The https://cern.ch/caimira application is running on CERN's OpenShift platform. In order to set it up for the first time, we followed the documentation at https://cern.service-now.com/service-portal?id=kb_article&n=KB0004498. In particular we:

 * Added the OpenShift application deploy key to the GitLab repository
 * Created a Python 3.6 (the highest possible at the time of writing) application in OpenShift
 * Configured a generic webhook on OpenShift, and call that from the CI of the GitLab repository

### Updating the caimira-test.web.cern.ch instance

We have a replica of https://caimira.web.cern.ch running on http://caimira-test.web.cern.ch. Its purpose is to simulate what will happen when
a feature is merged. To push your changes to caimira-test, simply push your branch to `live/caimira-test` and the CI pipeline will trigger the
deployment. To push to this branch, there is a good chance that you will need to force push - you should always force push with care and
understanding why you are doing it. Syntactically, it will look something like (assuming that you have "upstream" as your remote name,
but it may be origin if you haven't configured it differently):

    git push --force upstream name-of-local-branch:live/caimira-test


## OpenShift templates

### First setup

First, get the [oc](https://docs.okd.io/3.11/cli_reference/get_started_cli.html) client and then login:

```console
$ oc login https://api.paas.okd.cern.ch
```

Then, switch to the project that you want to update:

```console
$ oc project caimira-test
```

Create a new service account in OpenShift to use GitLab container registry:

```console
$ oc create serviceaccount gitlabci-deployer
serviceaccount "gitlabci-deployer" created

$ oc policy add-role-to-user registry-editor -z gitlabci-deployer

# We will refer to the output of this command as `test-token`
$ oc serviceaccounts get-token gitlabci-deployer
<...test-token...>
```

Add the token to GitLab to allow GitLab to access OpenShift and define/change image stream tags. Go to `Settings` -> `CI / CD` -> `Variables` -> click on `Expand` button and create the variable `OPENSHIFT_CAIMIRA_TEST_DEPLOY_TOKEN`: insert the token `<...test-token...>`.

Then, create the webhook secret to be able to trigger automatic builds from GitLab.

Create and store the secret. Copy the secret above and add it to the GitLab project under `CI /CD` -> `Variables` with the name `OPENSHIFT_CAIMIRA_TEST_WEBHOOK_SECRET`.

```console
$ WEBHOOKSECRET=$(openssl rand -hex 50)
$ oc create secret generic \
  --from-literal="WebHookSecretKey=$WEBHOOKSECRET" \
  gitlab-caimira-webhook-secret
```

For CI usage, we also suggest creating a service account:

```console
oc create sa gitlab-config-checker
```

Under ``User Management`` -> ``RoleBindings`` create a new `RoleBinding` to grant `View` access to the `gitlab-config-checker` service account:

* name: `gitlab-config-checker-view-role`
* role name: `view`
* service account: `gitlab-config-checker`

To get this new user's authentication token go to ``User Management`` -> ``Service Accounts`` -> `gitlab-config-checker` and locate the token in the newly created secret associated with the user (in this case ``gitlab-config-checker-token-XXXX``). Copy the `token` value from `Data`.

Create the various configurations:

```console
$ cd app-config/openshift

$ oc process -f configmap.yaml | oc create -f -
$ oc process -f services.yaml | oc create -f -
$ oc process -f imagestreams.yaml | oc create -f -
$ oc process -f buildconfig.yaml --param GIT_BRANCH='live/caimira-test' | oc create -f -
$ oc process -f deploymentconfig.yaml --param PROJECT_NAME='caimira-test'  | oc create -f -
```

### CERN SSO integration

The SSO integration uses OpenID credentials configured in [CERN Applications portal](https://application-portal.web.cern.ch/).
How to configure the application:

* Application Identifier: `caimira-test`
* Homepage: `https://caimira-test.web.cern.ch`
* Administrators: `caimira-dev`
* SSO Registration:
    * Protocol: `OpenID (OIDC)`
    * Redirect URI: `https://caimira-test.web.cern.ch/auth/authorize`
    * Leave unchecked all the other checkboxes
* Define new roles:
    * Name: `CERN Users`
        * Role Identifier: `external-users`
        * Leave unchecked checkboxes
        * Minimum Level Of Assurance: `CERN (highest)`
        * Assign role to groups: `cern-accounts-primary` e-group
    * Name: `External accounts`
        * Role Identifier: `admin`
        * Leave unchecked checkboxes
        * Minimum Level Of Assurance: `Any (no restrictions)`
        * Assign role to groups: `caimira-app-external-access` e-group
    * Name: `Allowed users`
        * Role Identifier: `allowed-users`
        * Check `This role is required to access my application`
        * Minimum Level Of Assurance:`Any (no restrictions)`
        * Assign role to groups: `cern-accounts-primary` and `caimira-app-external-access` e-groups

Copy the client id and client secret and use it below.

```console
$ COOKIE_SECRET=$(openssl rand -hex 50)
$ oc create secret generic \
  --from-literal="CLIENT_ID=$CLIENT_ID" \
  --from-literal="CLIENT_SECRET=$CLIENT_SECRET" \
  --from-literal="COOKIE_SECRET=$COOKIE_SECRET" \
  auth-service-secrets
```

### External APIs

- **Geographical location:**
There is one external API call to fetch required information related to the geographical location inserted by a user.
The documentation for this geocoding service is available at https://developers.arcgis.com/rest/geocode/api-reference/geocoding-suggest.htm . 
Please note that there is no need for keys on this API call. It is **free-of-charge**.

- **Humidity and Inside Temperature:**
There is the possibility of using one external API call to fetch information related to a location specified in the UI. The data is related to the inside temperature and humidity taken from an indoor measurement device. Note that the API currently used from ARVE is only available for the `CERN theme` as the authorised sensors are installed at CERN." 

## Update configuration

If you need to **update** existing configuration, then modify this repository and after having logged in, run:

```console
$ cd app-config/openshift


$ oc process -f configmap.yaml | oc replace -f -
$ oc process -f services.yaml | oc replace -f -
$ oc process -f imagestreams.yaml | oc replace -f -
$ oc process -f buildconfig.yaml --param GIT_BRANCH='live/caimira-test' | oc replace -f -
$ oc process -f deploymentconfig.yaml --param PROJECT_NAME='caimira-test' | oc replace -f -
```

Be aware that if you create/recreate the environment you must manually create a **route** in OpenShift, 
specifying the respective annotation to be exposed outside CERN.
