#!/usr/bin/env bash
# Idempotent setup for the MGT 409 homework environment.
# Safe to run repeatedly: apt install, venv creation, and pip install all no-op
# when the state is already present.
set -euo pipefail

cd "$(dirname "$0")/.."

# System dependency: the base image ships Python 3.12 but not the venv module.
if ! dpkg -s python3.12-venv >/dev/null 2>&1; then
  echo "Installing python3.12-venv..."
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3.12-venv
fi

# Create the virtual environment if it does not already exist.
if [ ! -x ".venv/bin/python" ]; then
  echo "Creating virtual environment in .venv..."
  python3 -m venv .venv
fi

# Install/refresh dependencies and the local package (editable).
echo "Installing Python dependencies..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .

echo "Install complete. Activate with: source .venv/bin/activate"
