
echo 'CAiMIRA is running on http://localhost:8080'
echo 'Please see https://gitlab.cern.ch/caimira/caimira for terms of use.'

# Run a proxy for the apps (listening on 8080).
nginx -c /opt/caimira/nginx.conf

# Run the expert app in the background.
cd /opt/caimira/src/caimira
/opt/caimira/app/bin/python -m voila /opt/caimira/src/caimira/apps/expert/caimira.ipynb \
  --port=8082 --no-browser --base_url=/voila-server/ \
  --Voila.tornado_settings 'allow_origin=*' \
  >> /var/log/expert-app.log 2>&1 &

/opt/caimira/app/bin/python -m voila /opt/caimira/src/caimira/apps/expert_co2/caimira.ipynb \
  --port=8083 --no-browser --base_url=/co2-voila-server/ \
  --Voila.tornado_settings 'allow_origin=*' \
  >> /var/log/co2-app.log 2>&1 &

# Run the calculator in the foreground.
/opt/caimira/app/bin/python -m caimira.apps.calculator --port 8081 --no-debug
