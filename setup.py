# This module is part of CARA. Please see the repository at
# https://gitlab.cern.ch/cara/cara for details of the license and terms of use.
"""
setup.py for CARA.

For reference see
https://packaging.python.org/guides/distributing-packages-using-setuptools/

"""
from pathlib import Path
from setuptools import setup, find_packages


HERE = Path(__file__).parent.absolute()
with (HERE / 'README.md').open('rt') as fh:
    LONG_DESCRIPTION = fh.read().strip()


REQUIREMENTS: dict = {
    'core': [
        'dataclasses; python_version < "3.7"',
        'ipykernel',
        'ipympl != 0.8.0, != 0.8.1',
        'ipywidgets',
        'Jinja2',
        'loky',
        'matplotlib',
        'memoization',
        'mistune',
        'numpy',
        'psutil',
        'python-dateutil',
        'scipy',
        'sklearn',
        'timezonefinder',
        'tornado',
        'voila >=0.2.4',
    ],
    'app': [],
    'test': [
        'pytest',
        'pytest-mypy',
        'pytest-tornasync',
        'numpy-stubs @ git+https://github.com/numpy/numpy-stubs.git',
        'types-dataclasses',
        'types-python-dateutil',
    ],
    'dev': [
        'jupyterlab',
    ],
    'doc': [
        'sphinx',
        'sphinx_rtd_theme',
    ],
}


setup(
    name='CARA',
    version="1.0.0",

    maintainer='Andre Henriques',
    maintainer_email='andre.henriques@cern.ch',
    description='COVID Airborne Risk Assessment',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='cern.ch/cara',

    packages=find_packages(),
    python_requires='~=3.9',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",  # Apache 2.0
    ],

    install_requires=REQUIREMENTS['core'],
    extras_require={
        **REQUIREMENTS,
        # The 'dev' extra is the union of 'test' and 'doc', with an option
        # to have explicit development dependencies listed.
        'dev': [req
                for extra in ['dev', 'test', 'doc']
                for req in REQUIREMENTS.get(extra, [])],
        # The 'all' extra is the union of all requirements.
        'all': [req for reqs in REQUIREMENTS.values() for req in reqs],
    },
    package_data={'cara': [
        'apps/*/*',
        'apps/*/*/*',
        'apps/*/*/*/*',
        'apps/*/*/*/*/*',
        'data/*.json',
        'data/*.txt',
    ]},
)
