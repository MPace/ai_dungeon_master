#!/bin/bash

# Script to run the memory architecture tests


# Ensure the script is executable
chmod +x app/tests/memory/*.py

# Activate the virtual environment if available
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install pytest if it's not already installed
pip install pytest pytest-cov

# Run the tests with coverage
echo "Running memory architecture tests with coverage..."
python -m pytest app/tests/memory -v --cov=app.services.embedding_service --cov=app.services.memory_service --cov=app.services.memory_service_enhanced --cov=app.services.summarization_service --cov=app.services.langchain_service --cov-report=term-missing

# Run the end-to-end test separately with more verbose output
echo "Running end-to-end memory tests..."
python -m pytest app/tests/memory/test_memory_e2e.py -v

# Print completion message
echo "Memory architecture testing completed!"