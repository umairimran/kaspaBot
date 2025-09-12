#!/usr/bin/env python3
"""
Simple entry point for Kaspa RAG backend with integrated Twitter bot.
Run with: python main.py (make sure venv is activated)
"""

import sys
import os
import time
import threading

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from api import app
from twitter_bot_integration import bot_manager

def start_twitter_bot_async():
    """Start Twitter bot in background after a short delay"""
    time.sleep(3)  # Wait for API to be ready
    print("🤖 Starting Twitter bot...")
    result = bot_manager.start_bot()
    if result["success"]:
        print("✅ Twitter bot started successfully")
    else:
        if result.get("missing_credentials"):
            print("⚠️ Twitter bot not started - missing API credentials")
            print("   Set these environment variables to enable Twitter bot:")
            print("   - TWITTER_BEARER_TOKEN")
            print("   - TWITTER_API_KEY")
            print("   - TWITTER_API_SECRET") 
            print("   - TWITTER_ACCESS_TOKEN")
            print("   - TWITTER_ACCESS_TOKEN_SECRET")
        else:
            print(f"⚠️ Twitter bot failed to start: {result['message']}")

if __name__ == "__main__":
    print("🚀 Starting Kaspa RAG Backend with Twitter Bot...")
    print("📡 API will be available at: " + os.getenv("BACKEND_URL"))
    print("📝 API docs at: " + os.getenv("BACKEND_URL") + "/docs")
    print("🤖 Twitter bot will start automatically")
    print("⚡ Press Ctrl+C to stop")
    print("-" * 50)
    
    # Start Twitter bot in background thread
    bot_thread = threading.Thread(target=start_twitter_bot_async, daemon=True)
    bot_thread.start()
    
    try:
        # Use BACKEND_URL env var to determine host/port if available, else default to 0.0.0.0:8001
        from urllib.parse import urlparse

        backend_url = os.getenv("BACKEND_BIND_URL", "http://0.0.0.0:8000")
        parsed = urlparse(backend_url)
        host = parsed.hostname or "0.0.0.0"
        port = parsed.port or 8001

        uvicorn.run(
            "api:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        # Stop Twitter bot gracefully
        bot_manager.stop_bot()
        print("✅ Shutdown complete")
