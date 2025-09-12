#!/bin/bash
# Simple startup script for Kaspa RAG Backend

echo "🚀 Starting Kaspa RAG Backend..."

# Activate virtual environment
source ../venv/bin/activate

# Run the server
python main.py
