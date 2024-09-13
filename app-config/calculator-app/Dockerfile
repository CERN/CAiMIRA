FROM registry.cern.ch/docker.io/condaforge/mambaforge AS conda

ARG PYTHON_VERSION=3.12
RUN mamba create --yes -p /opt/app python=${PYTHON_VERSION}

COPY . /opt/app-source
WORKDIR /opt/app-source
# install Python deps
RUN cd cern_caimira \
    && conda run -p /opt/app python -m pip install -r requirements.txt
RUN cd caimira \
    && conda run -p /opt/app python -m pip install .
RUN cd cern_caimira \
    && conda run -p /opt/app python -m pip install .

COPY app-config/calculator-app/app.sh /opt/app/bin/calculator-app.sh

RUN cd /opt/app \
    && find -name '*.a' -delete \
    && rm -rf /opt/app/conda-meta \
    && rm -rf /opt/app/include \
    && find -name '__pycache__' -type d -exec rm -rf '{}' '+' \
    && rm -rf /opt/app/lib/python*/site-packages/pip /opt/app/lib/python*/idlelib /opt/app/lib/python*/ensurepip \
          /opt/app/bin/x86_64-conda-linux-gnu-ld \
          /opt/app/bin/sqlite3 \
          /opt/app/bin/openssl \
          /opt/app/share/terminfo \
    && find /opt/app/lib/ -name 'tests' -type d -exec rm -rf '{}' '+' \
    && find /opt/app/lib -name '*.pyx' -delete \
    ;

FROM registry.cern.ch/docker.io/library/debian

COPY --from=conda /opt/app /opt/app
ENV PATH=/opt/app/bin/:$PATH
# Make a convenient location to the installed CAiMIRA package (i.e. a directory called caimira in the CWD).
# It is important that this directory is also writable by a non-root user.
RUN mkdir -p /scratch \
  && chmod a+wx /scratch
# Set the HOME directory to something that anybody can write to (to support non root users, such as on openshift).
ENV HOME=/scratch
WORKDIR /scratch
RUN CERN_CAIMIRA_INIT_FILE=$(python -c "import cern_caimira; print(cern_caimira.__file__)") \
    && ln -s $(dirname ${CERN_CAIMIRA_INIT_FILE}) /scratch/cern_caimira
CMD [ "calculator-app.sh" ]
