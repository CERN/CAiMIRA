FROM registry.cern.ch/docker.io/library/python:3.9

# Copy just the requirements.txt initially, allowing Docker effectively to cache the build (good for dev).
COPY ./requirements.txt  /tmp/requirements.txt

RUN python -m venv /opt/caimira/app
RUN sed '/\.\[/d' -i /tmp/requirements.txt && /opt/caimira/app/bin/pip install -r /tmp/requirements.txt
RUN apt-get update && apt-get install -y nginx

# Now that we have done the installation of the dependencies, copy the caimira source.
COPY ./ /opt/caimira/src
COPY ./app-config/caimira-public-docker-image/run_caimira.sh /opt/caimira/start.sh

# To ensure that we have installed the full requirements, re-run the pip install.
# In the best case this will be a no-op.
RUN cd /opt/caimira/src/ && /opt/caimira/app/bin/pip install -r /opt/caimira/src/requirements.txt
RUN /opt/caimira/app/bin/jupyter trust /opt/caimira/src/caimira/apps/expert/*.ipynb
COPY ./app-config/caimira-public-docker-image/nginx.conf /opt/caimira/nginx.conf

EXPOSE 8080
ENTRYPOINT ["/bin/sh", "-c", "/opt/caimira/start.sh"]
