#!/bin/bash

# Script to run the memory architecture tests

# Create the test directory if it doesn't exist
mkdir -p tests/memory

# Copy the test files to the test directory
cp test_embedding_service.py tests/memory/
cp test_memory_service.py tests/memory/
cp test_memory_service_enhanced.py tests/memory/
cp test_summarization_service.py tests/memory/
cp test_langchain_integration.py tests/memory/
cp test_memory_e2e.py tests/memory/
cp conftest.py tests/

# Ensure the script is executable
chmod +x tests/memory/*.py

# Activate the virtual environment if available
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install pytest if it's not already installed
pip install pytest pytest-cov

# Run the tests with coverage
echo "Running memory architecture tests with coverage..."
python -m pytest tests/memory -v --cov=app.services.embedding_service --cov=app.services.memory_service --cov=app.services.memory_service_enhanced --cov=app.services.summarization_service --cov=app.services.langchain_service --cov-report=term-missing

# Run the end-to-end test separately with more verbose output
echo "Running end-to-end memory tests..."
python -m pytest tests/memory/test_memory_e2e.py -v

# Print completion message
echo "Memory architecture testing completed!"