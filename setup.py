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
        'ipympl',
        'ipywidgets',
        'Jinja2',
        'matplotlib',
        'mistune',
        'numpy',
        'qrcode[pil]',
        'tornado',
        'voila >=0.2.4',
    ],
    'app': [],
    'test': [
        'pytest',
        'pytest-mypy',
        'pytest-tornasync',
        'numpy-stubs @ git+https://github.com/numpy/numpy-stubs.git',
    ],
    'dev': [
        'jupyterlab',
    ],
}


setup(
    name='CARA',
    version="0.0.1.dev0",

    maintainer='Andre Henriques',
    maintainer_email='andre.henriques@cern.ch',
    description='COVID Airborne Risk Assessment',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='cern.ch/cara',

    packages=find_packages(),
    python_requires='~=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
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
        'apps/calculator/*',
        'apps/calculator/*/*',
        'apps/calculator/*/*/*'
    ]},
)
