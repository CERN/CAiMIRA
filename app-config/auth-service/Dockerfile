FROM registry.cern.ch/docker.io/condaforge/mambaforge as conda

RUN mamba create --yes -p /opt/app python=3.9
COPY . /opt/app-source
RUN conda run -p /opt/app python -m pip install /opt/app-source
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
CMD [ \
  "/opt/app/bin/python", "-m", "auth_service" \
]
