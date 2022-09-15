git clone https://gitlab.cern.ch/cara/caimira.git
cd caimira
pip install -e .
echo "############################################"
echo "CAiMIRA is now running at http://localhost:8080"
echo "############################################"
python -m caimira.apps.calculator

