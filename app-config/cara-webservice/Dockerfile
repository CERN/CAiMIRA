FROM condaforge/mambaforge as conda

RUN mamba create --yes -p /opt/app python=3.9
COPY . /opt/app-source
RUN cd /opt/app-source && conda run -p /opt/app python -m pip install -r ./requirements.txt .[app]
COPY app-config/cara-webservice/app.sh /opt/app/bin/cara-app.sh
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

FROM debian

COPY --from=conda /opt/app /opt/app
ENV PATH=/opt/app/bin/:$PATH
# Make a convenient location to the installed CARA package (i.e. a directory called cara in the CWD).
# It is important that this directory is also writable by a non-root user.
RUN mkdir -p /scratch \
 && chmod a+wx /scratch
# Set the HOME directory to something that anybody can write to (to support non root users, such as on openshift).
ENV HOME=/scratch
WORKDIR /scratch
RUN CARA_INIT_FILE=$(/opt/app/bin/python -c "import cara; print(cara.__file__)") \
 && ln -s $(dirname ${CARA_INIT_FILE}) /scratch/cara
CMD [ \
  "cara-app.sh" \
]
