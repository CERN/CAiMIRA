FROM python:3.9

COPY ./ /opt/cara/src
RUN python -m venv /opt/cara/app
RUN cd /opt/cara/src && /opt/cara/app/bin/pip install -r /opt/cara/src/requirements.txt
EXPOSE 8080
ENTRYPOINT ["/bin/sh", "-c", "echo 'CARA is running on http://localhost:8080' && echo 'Please see https://gitlab.cern.ch/cara/cara for terms of use.' && /opt/cara/app/bin/python -m cara.apps.calculator --no-debug"]
