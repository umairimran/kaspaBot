import requests

BACKEND_URL = "http://localhost:8000/ask"

def ask_backend(question: str):
    try:
        response = requests.post(BACKEND_URL, json={"question": question}, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("answer", "No answer received."), data.get("citations", [])
    except Exception as e:
        return f"Error: {e}", []
