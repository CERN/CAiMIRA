#!/bin/bash

if [[ "$APP_NAME" == "caimira-webservice" ]]; then
    args=("$@")
    if [ "$DEBUG" != "true" ] && [[ ! "${args[@]}" =~ "--no-debug" ]]; then
        args+=("--no-debug")
    fi

    if [ ! -z "$CAIMIRA_THEME" ]; then
        args+=("--theme=${CAIMIRA_THEME}")
    fi

    if [ ! -z "$CAIMIRA_CALCULATOR_PREFIX" ]; then
        args+=("--prefix=${CAIMIRA_CALCULATOR_PREFIX}")
    fi
    
    export "ARVE_API_KEY"="$ARVE_API_KEY"
    export "ARVE_CLIENT_ID"="$ARVE_CLIENT_ID"
    export "ARVE_CLIENT_SECRET"="$ARVE_CLIENT_SECRET"

    echo "Starting the caimira webservice with: python -m caimira.apps.calculator ${args[@]}"
    python -m caimira.apps.calculator "${args[@]}"
elif [[ "$APP_NAME" == "caimira-voila" ]]; then
    echo "Starting the voila service"
    voila caimira/apps/expert/ --port=8080 --no-browser --base_url=/voila-server/ --tornado_settings 'allow_origin=*'
else
    echo "No APP_NAME specified"
    exit 1
fi

