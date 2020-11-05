env
if [[ "$APP_NAME" == "cara-webservice" ]]; then
    echo "Starting the cara webservice"
    python -m cara.apps.calculator
elif [[ "$APP_NAME" == "cara-voila" ]]; then
    echo "Starting the voila service"
    voila app/ --port=8080 --no-browser --base_url=/voila-server/ --Voila.tornado_settings="{'allow_origin': '*'}"
fi

