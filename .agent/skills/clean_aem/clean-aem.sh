#!/bin/bash
# Skill: clean-aem
# Description: Cleans the Maven build and removes old AEM logs to save space.
# Usage: ./clean-aem.sh [--skip-mvn] [--skip-logs]

ENABLE_MVN=true
ENABLE_LOGS=true

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-mvn) ENABLE_MVN=false ;;
        --skip-logs) ENABLE_LOGS=false ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [ "$ENABLE_MVN" = true ]; then
    echo "Cleaning Maven project..."
    mvn clean
else
    echo "Skipping Maven clean."
fi

if [ "$ENABLE_LOGS" = true ]; then
    echo "Cleaning old AEM logs (older than 7 days)..."
    if [ -d "crx-quickstart/logs" ]; then
        find crx-quickstart/logs -type f -name "*.log" -mtime +7 -print -delete
        echo "Done cleaning logs."
    else
        echo "No crx-quickstart/logs directory found. Skipping log cleanup."
    fi
else
    echo "Skipping log cleanup."
fi
