#!/bin/bash

# Exit on error
set -e

# Print commands
set -x

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install transformers torch sentencepiece tqdm

# Run the download script
echo "Downloading models..."
python scripts/download_models.py

echo "Model download complete!" 