# Upgrading to Python 3.12

This project has been upgraded to require Python 3.12 (latest stable version).

## Installation Steps

### 1. Install Python 3.12

Run the installation script:

```bash
bash scripts/install_python312.sh
```

Or manually:

```bash
# Add deadsnakes PPA for newer Python versions
sudo add-apt-repository ppa:deadsnakes/ppa -y

# Update package list
sudo apt update

# Install Python 3.12 and essential packages
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3.12-distutils

# Install pip for Python 3.12
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
```

### 2. Verify Installation

```bash
python3.12 --version
# Should output: Python 3.12.x
```

### 3. Recreate Virtual Environment

Remove the old virtual environment and create a new one with Python 3.12:

```bash
# Remove old venv
rm -rf venv

# Create new venv with Python 3.12
python3.12 -m venv venv

# Activate the new venv
source venv/bin/activate

# Verify Python version
python --version
# Should output: Python 3.12.x

# Install project dependencies
pip install -e .
```

### 4. Verify Everything Works

```bash
# After activation, test the CLI
python -m tinyseoai --help
```

## What Changed

- `pyproject.toml`: Updated `requires-python` from `>=3.10` to `>=3.12`
- `pyproject.toml`: Updated Black target version from `py311` to `py312`
- `pyproject.toml`: Updated MyPy Python version from `3.11` to `3.12`

## Notes

- Python 3.12 is the latest stable version as of 2025
- The old virtual environment (Python 3.10) should be removed before creating the new one
- All dependencies will be reinstalled with Python 3.12

