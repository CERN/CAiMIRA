
echo 'CAiMIRA is running on http://localhost:8080'
echo 'Please see https://gitlab.cern.ch/caimira/caimira for terms of use.'

# Run a proxy for the apps (listening on 8080).
nginx -c /opt/caimira/nginx.conf

cd /opt/caimira/src/caimira
# Run the calculator in the foreground.
/opt/caimira/app/bin/python -m ui.apps.calculator --port 8081 --no-debug
