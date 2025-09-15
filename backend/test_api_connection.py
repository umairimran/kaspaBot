#!/usr/bin/env python3
"""
Test script to verify the backend API connection from Twitter bot
"""

import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Get BACKEND_URL from environment
BACKEND_URL = os.getenv("BACKEND_URL")
print(f"🔍 Testing connection to: {BACKEND_URL}")

def test_api_connection():
    """Test connection to backend API"""
    try:
        # Simple status check
        status_url = f"{BACKEND_URL}/status"
        print(f"📡 Calling status endpoint: {status_url}")
        
        status_response = requests.get(status_url, timeout=10)
        print(f"📊 Status response code: {status_response.status_code}")
        
        if status_response.status_code == 200:
            print(f"✅ Status endpoint successful!")
            print(f"📝 Response: {json.dumps(status_response.json(), indent=2)}")
        else:
            print(f"❌ Status endpoint failed with code {status_response.status_code}")
            print(f"📝 Response: {status_response.text}")
        
        # Test the /ask endpoint
        ask_url = f"{BACKEND_URL}/ask"
        print(f"\n📡 Calling ask endpoint: {ask_url}")
        
        payload = {
            "question": "What is Kaspa?",
            "conversation_id": "test_connection",
            "user_id": "test_user"
        }
        
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        
        ask_response = requests.post(ask_url, json=payload, timeout=30)
        print(f"📊 Ask response code: {ask_response.status_code}")
        
        if ask_response.status_code == 200:
            print(f"✅ Ask endpoint successful!")
            response_data = ask_response.json()
            print(f"📝 Answer: {response_data.get('answer', '')[:100]}...")
        else:
            print(f"❌ Ask endpoint failed with code {ask_response.status_code}")
            print(f"📝 Response: {ask_response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print(f"💡 This usually means the backend is not accessible at {BACKEND_URL}")
        print(f"💡 Check that:")
        print(f"   - The backend is running")
        print(f"   - BACKEND_URL is correct in your .env file")
        print(f"   - The port is open in your firewall")
        print(f"   - If using a public IP, ensure it's accessible")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if not BACKEND_URL:
        print("❌ BACKEND_URL not found in environment variables")
        print("💡 Make sure you have BACKEND_URL set in your .env file")
    else:
        test_api_connection()
