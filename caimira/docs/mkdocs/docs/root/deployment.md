The [https://cern.ch/caimira](https://cern.ch/caimira) application is running on CERN's OpenShift platform. In order to set it up for the first time, we followed the documentation at [https://paas.docs.cern.ch/](https://paas.docs.cern.ch/). In particular we:

 * Added the OpenShift application deploy key to the GitLab repository
 * Created a Python 3.12 (the highest possible at the time of writing) application in OpenShift
 * Configured a generic webhook on OpenShift, and call that from the CI of the GitLab repository

## OpenShift templates

For the first setup, get the [oc](https://docs.okd.io/3.11/cli_reference/get_started_cli.html) client and then login:

```console
$ oc login https://api.paas.okd.cern.ch
```

Then, switch to the project that you want to update:

```console
$ oc project caimira-test
```

Create a new service account in OpenShift to access GitLab container registry:

```console
$ oc create serviceaccount gitlabci-deployer
serviceaccount "gitlabci-deployer" created
```

Grant `edit` permission to the service account to run `oc set image` from CI an update the tag to deploy:
```
$ oc policy add-role-to-user edit -z gitlabci-deployer
```

Get the service account token for GitLab:
```
# We will refer to the output of this command as `test-token`
$ oc serviceaccounts get-token gitlabci-deployer
<...test-token...>
```

Add the token to GitLab to allow GitLab to access OpenShift and define/change image stream tags. Go to `Settings` -> `CI / CD` -> `Variables` -> click on `Expand` button and create the variable `OPENSHIFT_CAIMIRA_TEST_DEPLOY_TOKEN`: insert the token `<...test-token...>`.

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
$ oc process -f deployments.yaml  | oc create -f -
```

Manually create the **route** to access the website, see `routes.example.yaml`.
After having created the route, make sure that you extend the HTTP request timeout annotation: the
report generation can take more time than the default 30 seconds.

```
$ oc annotate route caimira-route --overwrite haproxy.router.openshift.io/timeout=60s
```

## CERN SSO integration

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

## Updating OpenShift configuration

If you need to **update** existing configuration, then modify this repository and after having logged in, run:

```console
$ cd app-config/openshift


$ oc process -f configmap.yaml | oc replace -f -
$ oc process -f services.yaml | oc replace -f -
$ oc process -f deployments.yaml | oc replace -f -
```

Be aware that if you create/recreate the environment you must manually create a **route** in OpenShift,
specifying the respective annotation to be exposed outside CERN.


## Updating the TEST instance

We have a replica of [https://caimira.web.cern.ch](https://caimira.web.cern.ch) running on [http://caimira-test.web.cern.ch](http://caimira-test.web.cern.ch). Its purpose is to simulate what will happen when
a feature is merged. To push your changes to caimira-test, simply push your branch to `live/caimira-test` and the CI pipeline will trigger the
deployment. To push to this branch, there is a good chance that you will need to force push - you should always force push with care and
understanding why you are doing it. Syntactically, it will look something like (assuming that you have "upstream" as your remote name,
but it may be origin if you haven't configured it differently):

    git push --force upstream name-of-local-branch:live/caimira-test

## Deployment Process

The deployment process varies depending on whether changes are pushed to branches, tags, or the test environment (`live/caimira-test` branch).

### Branch and Tag-based Deployment

For branch pushes:

* All branches (except `live/caimira-test`) trigger the **test** stage in the CI/CD pipeline, ensuring the code passes all necessary tests before it is deployed.

For tag creation:

* When a new tag is created, the pipeline skips the previous tests, and it builds `Docker` images, storing them in GitLab's container registry. The images can be manually deployed to the OKD platform for the `PROD` - production environment.

### OKD Platform Deployment
The `cern_caimira` package, which contains the CERN-specific UI, is deployed directly to the OKD platform. The `caimira package`, which contains the backend logic, is deployed as a standalone API for integration with external services.

### Versioning and Tags
The repository follows a *semantic versioning* scheme, with tags named according to the `MAJOR.MINOR.PATCH` format (e.g., `v5.0.0`).
