#!/bin/bash

args=("$@")
if [ "$DEBUG" != "true" ] && [[ ! "${args[@]}" =~ "--no-debug" ]]; then
    args+=("--no-debug")
fi

echo "Starting the caimira api app with: python -m caimira.api.app ${args[@]}"
python -m caimira.api.app "${args[@]}"
