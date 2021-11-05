cd Downloads
git clone https://gitlab.cern.ch/cara/cara.git
cd cara
git lfs pull
if [[ `uname -m` == 'arm64' ]]; then
  pip3 install scipy --index-url=https://pypi.anaconda.org/scipy-wheels-nightly/simple
  pip3 install -U --no-use-pep517 scikit-learn
fi
pip3 install -e .
python3 -m cara.apps.calculator