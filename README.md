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


## Disclaimer

The code and data of this repository are provided to promote reproducible research.
They are not intended for clinical care or commercial use.

The software is provided "as is", without warranty of any kind, express or implied,
including but not limited to the warranties of merchantability, fitness for a particular
purpose and non infringement.
In no event shall the authors or copyright holders be liable for any claim, damages
or other liability, whether in an action of contract, tort or otherwise, arising from,
out of or in connection with the software or the use or other dealings in the software.


## Development guide

### Running the COVID calculator app locally

```
pip install -e .   # At the root of the repository
python -m cara.apps.calculator
```

To run with the CERN theme:

```
python -m cara.apps.calculator --theme=cara/apps/calculator/themes/cern
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
s2i build file://$(pwd) --copy --keep-symlinks --context-dir ./ centos/python-36-centos7 cara-webservice
s2i build file://$(pwd) --copy --keep-symlinks --context-dir ./app-config/auth-service centos/python-36-centos7 auth-service
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
understanding why you are doing it. Syntactically, it will look something like (assuming that you have "upstream" as your remote name,
but it may be origin if you haven't configured it differently):

    git push --force upstream name-of-local-branch:live/test-cara


## OpenShift templates

### First setup

First, get the [oc](https://docs.okd.io/3.11/cli_reference/get_started_cli.html) client and then login:

```console
$ oc login https://openshift-dev.cern.ch
```

Then, switch to the project that you want to update:

```console
$ oc project test-cara
```

If you need to create the application in a new project, run:

```console
$ cd app-config/openshift

$ oc process -f application.yaml --param PROJECT_NAME='test-cara' --param GIT_BRANCH='live/test-cara' | oc create -f -
$ oc process -f configmap.yaml | oc create -f -
$ oc process -f services.yaml | oc create -f -
$ oc process -f route.yaml --param HOST='test-cara.web.cern.ch' | oc create -f -
```

Then, create the webhook secret to be able to trigger automatic builds from GitLab.

Create and store the secret. Copy the secret above and add it to the GitLab project under `CI /CD` -> `Variables` with the name `OPENSHIFT_CARA_TEST_WEBHOOK_SECRET`.

```console
$ WEBHOOKSECRET=$(openssl rand -hex 50)
$ oc create secret generic \
  --from-literal="WebHookSecretKey=$WEBHOOKSECRET" \
  gitlab-cara-webhook-secret
```

### CERN SSO integration

The SSO integration uses OpenID credentials configured in [CERN Applications portal](https://application-portal.web.cern.ch/).
How to configure the application:

* Application Identifier: `cara-test`
* Homepage: `https://test-cara.web.cern.ch`
* Administrators: `cara-dev`
* SSO Registration:
    * Protocol: `OpenID (OIDC)`
    * Redirect URI: `https://test-cara.web.cern.ch/auth/authorize`
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
        * Assign role to groups: `cara-app-external-access` e-group
    * Name: `Allowed users`
        * Role Identifier: `allowed-users`
        * Check `This role is required to access my application`
        * Minimum Level Of Assurance:`Any (no restrictions)`
        * Assign role to groups: `cern-accounts-primary` and `cara-app-external-access` e-groups

Copy the client id and client secret and use it below.

```console
$ COOKIE_SECRET=$(openssl rand -hex 50)
$ oc create secret generic \
  --from-literal="CLIENT_ID=$CLIENT_ID" \
  --from-literal="CLIENT_SECRET=$CLIENT_SECRET" \
  --from-literal="COOKIE_SECRET=$COOKIE_SECRET" \
  auth-service-secrets
```

## Update configuration

If you need to **update** existing configuration, then modify this repository and after having logged in, run:

```console
$ cd app-config/openshift

$ oc process -f application.yaml --param PROJECT_NAME='test-cara' --param GIT_BRANCH='live/test-cara' | oc replace -f -
$ oc process -f configmap.yaml | oc replace -f -
$ oc process -f services.yaml | oc replace -f -
$ oc process -f route.yaml --param HOST='test-cara.web.cern.ch' | oc replace -f -
```

Be aware that if you change/replace the **route** of the PROD instance, it will loose the annotation to be exposed outside CERN (not committed in this repo).
