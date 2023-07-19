#!/bin/bash

if [[ "$APP_NAME" == "calculator-app" ]]; then
    args=("$@")
    if [ "$DEBUG" != "true" ] && [[ ! "${args[@]}" =~ "--no-debug" ]]; then
        args+=("--no-debug")
    fi

    if [ ! -z "$APPLICATION_ROOT" ]; then
        args+=("--app_root=${APPLICATION_ROOT}")
    fi

    if [ ! -z "$CAIMIRA_CALCULATOR_PREFIX" ]; then
        args+=("--prefix=${CAIMIRA_CALCULATOR_PREFIX}")
    fi
    if [ ! -z "$CAIMIRA_THEME" ]; then
        args+=("--theme=${CAIMIRA_THEME}")
    fi
    
    export "ARVE_API_KEY"="$ARVE_API_KEY"
    export "ARVE_CLIENT_ID"="$ARVE_CLIENT_ID"
    export "ARVE_CLIENT_SECRET"="$ARVE_CLIENT_SECRET"

    export "EXTRA_PAGES"="$EXTRA_PAGES"

    export "DATA_SERVICE_ENABLED"="${DATA_SERVICE_ENABLED:=False}"
    export "DATA_SERVICE_CLIENT_EMAIL"="$DATA_SERVICE_CLIENT_EMAIL"
    export "DATA_SERVICE_CLIENT_PASSWORD"="$DATA_SERVICE_CLIENT_PASSWORD"

    echo "Starting the caimira webservice with: python -m caimira.apps.calculator ${args[@]}"
    python -m caimira.apps.calculator "${args[@]}"
elif [[ "$APP_NAME" == "caimira-voila" ]]; then
    echo "Starting the voila service"
    voila caimira/apps/expert/ --port=8080 --no-browser --base_url=/voila-server/ --tornado_settings 'allow_origin=*'
elif [[ "$APP_NAME" == "caimira-co2-voila" ]]; then
    echo "Starting the CO2 voila service"
    voila caimira/apps/expert_co2/ --port=8080 --no-browser --base_url=/co2-voila-server/ --tornado_settings 'allow_origin=*'
else
    echo "No APP_NAME specified"
    exit 1
fi

