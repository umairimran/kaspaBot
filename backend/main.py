#!/usr/bin/env python3
"""
Simple entry point for Kaspa RAG backend.
Run with: python main.py (make sure venv is activated)
"""

import sys
import os

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from api import app

if __name__ == "__main__":
    print("🚀 Starting Kaspa RAG Backend...")
    print("📡 API will be available at: http://localhost:8000")
    print("📝 API docs at: http://localhost:8000/docs")
    print("⚡ Press Ctrl+C to stop")
    print("-" * 50)
    
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
