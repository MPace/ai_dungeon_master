#!/bin/bash

# Exit on error
set -e

# Print commands
set -x

# Set up directories
MODEL_DIR="$HOME/ai_dungeon_models"
VENV_DIR="$HOME/ai_dungeon_venv"

# Create model directory if it doesn't exist
mkdir -p "$MODEL_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install required packages
echo "Installing required packages..."
pip install transformers torch sentencepiece tqdm

# Set environment variables for model downloads
export TRANSFORMERS_CACHE="$MODEL_DIR"
export HF_HOME="$MODEL_DIR"

# Run the download script
echo "Downloading models..."
python scripts/download_models.py

echo "Model download complete!"
echo "Models are stored in: $MODEL_DIR"
echo "Virtual environment is in: $VENV_DIR" 