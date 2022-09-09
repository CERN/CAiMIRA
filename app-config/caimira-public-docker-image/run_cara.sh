
echo 'CARA is running on http://localhost:8080'
echo 'Please see https://gitlab.cern.ch/cara/cara for terms of use.'

# Run a proxy for the apps (listening on 8080).
nginx -c /opt/cara/nginx.conf

# Run the expert app in the background.
cd /opt/cara/src/cara
/opt/cara/app/bin/python -m voila /opt/cara/src/cara/apps/expert/cara.ipynb \
  --port=8082 --no-browser --base_url=/voila-server/ \
  --Voila.tornado_settings 'allow_origin=*' \
  >> /var/log/expert-app.log 2>&1 &

# Run the calculator in the foreground.
/opt/cara/app/bin/python -m cara.apps.calculator --port 8081 --no-debug
