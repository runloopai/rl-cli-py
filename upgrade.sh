#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate the virtual environment
source "$(dirname "$0")/.venv/bin/activate"

# Ensure pip and pip-tools are up to date
pip install --upgrade pip pip-tools

# Upgrade main dependencies
echo "Upgrading main dependencies..."
pip-compile --upgrade pyproject.toml

# Upgrade dev dependencies
echo "Upgrading dev dependencies..."
pip-compile --upgrade --extra=dev --output-file=dev-requirements.txt pyproject.toml

# Deactivate the virtual environment
deactivate

echo "Dependencies have been upgraded. requirements.txt and dev-requirements.txt have been updated."