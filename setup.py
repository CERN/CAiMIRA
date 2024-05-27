# This module is part of CAiMIRA. Please see the repository at
# https://gitlab.cern.ch/caimira/caimira for details of the license and terms of use.
"""
setup.py for CAiMIRA.

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
        'ipympl >= 0.9.0',
        'ipywidgets < 8.0',
        'Jinja2',
        'loky',
        'matplotlib',
        'memoization',
        'mistune',
        'numpy',
        'pandas',
        'psutil',
        'pyjwt',
        'python-dateutil',
        'retry',
        'ruptures',
        'scipy',
        'scikit-learn',
        'timezonefinder',
        'tornado',
        'types-retry',
        'voila',
    ],
    'app': [],
    'test': [
        'pytest < 8.2',
        'pytest-mypy >= 0.10.3',
        'mypy >= 1.0.0',
        'pytest-tornasync',
        'numpy-stubs @ git+https://github.com/numpy/numpy-stubs.git',
        'types-dataclasses',
        'types-python-dateutil',
        'types-requests',
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
    name='CAiMIRA',
    version="1.0.0",

    maintainer='Andre Henriques',
    maintainer_email='andre.henriques@cern.ch',
    description='COVID Airborne Risk Assessment',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='cern.ch/caimira',

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
    package_data={'caimira': [
        'apps/*/*',
        'apps/*/*/*',
        'apps/*/*/*/*',
        'apps/*/*/*/*/*',
        'data/*.json',
        'data/*.txt',
    ]},
)
