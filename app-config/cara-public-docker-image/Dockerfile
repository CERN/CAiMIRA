FROM registry.cern.ch/docker.io/library/python:3.9

# Copy just the requirements.txt initially, allowing Docker effectively to cache the build (good for dev).
COPY ./requirements.txt  /tmp/requirements.txt

RUN python -m venv /opt/cara/app
RUN sed '/\.\[/d' -i /tmp/requirements.txt && /opt/cara/app/bin/pip install -r /tmp/requirements.txt
RUN apt-get update && apt-get install -y nginx

# Now that we have done the installation of the dependencies, copy the cara source.
COPY ./ /opt/cara/src
COPY ./app-config/cara-public-docker-image/run_cara.sh /opt/cara/start.sh

# To ensure that we have installed the full requirements, re-run the pip install.
# In the best case this will be a no-op.
RUN cd /opt/cara/src/ && /opt/cara/app/bin/pip install -r /opt/cara/src/requirements.txt
RUN /opt/cara/app/bin/jupyter trust /opt/cara/src/cara/apps/expert/*.ipynb
COPY ./app-config/cara-public-docker-image/nginx.conf /opt/cara/nginx.conf

EXPOSE 8080
ENTRYPOINT ["/bin/sh", "-c", "/opt/cara/start.sh"]
