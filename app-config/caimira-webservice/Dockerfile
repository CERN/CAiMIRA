FROM registry.cern.ch/docker.io/condaforge/mambaforge as conda

RUN mamba create --yes -p /opt/app python=3.9
COPY . /opt/app-source
RUN cd /opt/app-source && conda run -p /opt/app python -m pip install -r ./requirements.txt .[app]
COPY app-config/caimira-webservice/app.sh /opt/app/bin/caimira-app.sh
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
RUN CAIMIRA_INIT_FILE=$(/opt/app/bin/python -c "import cara; print(cara.__file__)") \
 && ln -s $(dirname ${CAIMIRA_INIT_FILE}) /scratch/caimira
CMD [ \
  "caimira-app.sh" \
]
