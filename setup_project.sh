#!/bin/bash
# Sting Operation AI — Linux/macOS setup script
set -e

echo "Setting up Sting Operation AI..."

python3.10 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install git+https://github.com/fivepanelhat/coastal-alpine-core.git@v0.1.0
pip install -r requirements.txt
pip install -r requirements-dev.txt

python tools/verify_setup.py

echo "Setup complete."
