#!/bin/bash
# Script to install Python 3.12 on Ubuntu 22.04
# Run with: bash scripts/install_python312.sh

set -e

echo "Installing Python 3.12..."

# Add deadsnakes PPA for newer Python versions
sudo add-apt-repository ppa:deadsnakes/ppa -y

# Update package list
sudo apt update

# Install Python 3.12 and essential packages
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3.12-distutils

# Install pip for Python 3.12
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

echo "Python 3.12 installed successfully!"
echo "Verify with: python3.12 --version"

