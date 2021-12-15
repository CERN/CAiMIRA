cd Downloads
git clone https://gitlab.cern.ch/cara/cara.git
cd cara
git lfs install
git lfs pull
if [[ `uname -m` == 'arm64' ]]; then
  pip3 install scipy --index-url=https://pypi.anaconda.org/scipy-wheels-nightly/simple
  pip3 install Cython
  pip3 install -U --no-use-pep517 scikit-learn
fi
pip3 install -e .
echo "############################################"
echo "CARA is now running at http://localhost:8080"
echo "############################################"
python3 -m cara.apps.calculator --theme=cara/apps/calculator/themes/cern