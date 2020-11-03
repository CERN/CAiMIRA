# CARA - COVID Airborne Risk Assessment



## Credits


## Development guide

### Building the docker image for local execution

**Simulate the docker build that takes place on openshift with:**

```
s2i build file://$(pwd) --copy --context-dir=app-config/nginx/ centos/nginx-112-centos7 cara-nginx-app
s2i build file://$(pwd) --copy --context-dir=./ centos/python-36-centos7 cara-voila-app
cd app-config
docker-compose up
```

Then visit localhost:8080.

### Setting up the application

The https://cern.ch/cara application is running on CERN's OpenShift platform. In order to set it up for the first time, we followed the documentation at https://cern.service-now.com/service-portal?id=kb_article&n=KB0004498. In particular we:

 * Added the OpenShift application deploy key to the GitLab repository
 * Created a Python 3.6 (the highest possible at the time of writing) application in OpenShift
 * Configured a generic webhook on OpenShift, and call that from the CI of the GitLab repository


