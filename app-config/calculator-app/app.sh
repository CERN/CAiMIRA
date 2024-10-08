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

    export "DATA_SERVICE_ENABLED"="${DATA_SERVICE_ENABLED:=0}"
    export "CAIMIRA_PROFILER_ENABLED"="${CAIMIRA_PROFILER_ENABLED:=0}"

    echo "Starting the caimira calculator app with: python -m cern_caimira.apps.calculator ${args[@]}"
    python -m cern_caimira.apps.calculator "${args[@]}"

else
    echo "No APP_NAME specified"
    exit 1
fi

