#!/bin/bash

if [[ "$APP_NAME" == "cara-webservice" ]]; then
    args=("$@")
    if [ "$DEBUG" != "true" ] && [[ ! "${args[@]}" =~ "--no-debug" ]]; then
        args+=("--no-debug")
    fi

    if [ ! -z "$CARA_THEME" ]; then
        args+=("--theme=${CARA_THEME}")
    fi

    if [ ! -z "$CARA_CALCULATOR_PREFIX" ]; then
        args+=("--prefix=${CARA_CALCULATOR_PREFIX}")
    fi

    echo "Starting the cara webservice with: python -m cara.apps.calculator ${args[@]}"
    python -m cara.apps.calculator "${args[@]}"
elif [[ "$APP_NAME" == "cara-voila" ]]; then
    echo "Starting the voila service"
    voila app/ --port=8080 --no-browser --base_url=/voila-server/ --Voila.tornado_settings="{'allow_origin': '*'}"
else
    echo "No APP_NAME specified"
    exit 1
fi

