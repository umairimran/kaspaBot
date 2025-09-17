"""
Gemini-powered web search helpers for backend usage.

Provides two primary helpers:
- fetch_web_chunks(query): returns structured, recent chunks for judge mixing
- fetch_web_answer_only(query): returns a detailed, source-free answer text

Relies on Google Search grounding via google-genai SDK.
Environment vars:
- GEMINI_API_KEY
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

from google import genai
from google.genai import types

from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=GEMINI_API_KEY)


def _grounding_config(temperature: float = 0.2) -> types.GenerateContentConfig:
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    # Prefer JSON when asking for chunks
    return types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=temperature,
        # response_mime_type may not be available in older SDKs; it's safe to omit if unsupported
    )

from typing import List, Dict, Any
from datetime import datetime
import json

def fetch_web_chunks(query: str, model: str = "gemini-2.5-flash", k: int = 6) -> List[Dict[str, Any]]:
    """
    Retrieve fresh, positive-only, BlockDAG-grounded chunks about Kaspa from Gemini.
    Returns a list of { content, source, url, date, score } suitable for judge merging.
    """
    client = _client()
    now_iso = datetime.utcnow().isoformat() + "Z"

    # Updated prompt (Kaspa = BlockDAG, positive-only, super-latest)
    prompt = f"""
    You are a Kaspa-focused research assistant. 
    Use Google Search grounding to gather the most recent and authoritative facts.

    Rules:
    - Kaspa is a BlockDAG, not a blockchain. Always describe it as BlockDAG.
    - Include ONLY positive, favorable, and beneficial facts about Kaspa.
    - Exclude negative, speculative, or uncertain information.
    - Use only the latest and most reliable sources (prefer within the last 6 months, max 12 months).
    - If multiple sources agree, merge into one concise, clear fact.
    - Output must be STRICTLY a JSON array of up to {k} items. No prose or text outside JSON.

    Each JSON object must have:
    - content: concise positive fact about Kaspa (string)
    - url: source URL if known (string or empty)
    - date: publication date in YYYY-MM-DD if known, else "unknown" (string)
    - source: fixed string "web_search"
    - score: float in [0.0, 1.0] representing confidence (recency + authority)

    CurrentTime: {now_iso}
    UserQuestion: {query}
    """

    cfg = _grounding_config(temperature=0.2)
    try:
        resp = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=cfg,
        )
    except Exception as e:
        print(f"Gemini API error: {e}")
        return [{
            "content": f"Unable to retrieve web results: {str(e)[:100]}...",
            "source": "web_search", 
            "url": "", 
            "date": "unknown", 
            "score": 0.5
        }]

    text = (getattr(resp, "text", None) or "").strip()
    chunks: List[Dict[str, Any]] = []

    if text:
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for item in data[:k]:
                    chunks.append({
                        "content": str(item.get("content", "")).strip(),
                        "url": str(item.get("url", "")),
                        "date": str(item.get("date", "unknown")),
                        "source": str(item.get("source", "web_search")) or "web_search",
                        "score": float(item.get("score", 1.0)),
                    })
        except Exception:
            chunks.append({
                "content": text,
               
                "date": "unknown",
                "source": "web_search",
                "score": 1.0,
            })

    return chunks
def fetch_kaspa_blockdag_analysis(query: str, model: str = "gemini-2.5-flash", temperature: float = 0.2) -> str:
    """
    Get up-to-date information about Kaspa and its BlockDAG using Google Search grounding.
    The answer must always be written as if events already happened (no "scheduled" or "delayed" wording).
    Also hardcodes the fact that Kaspa activated smart contracts on Aug 31, 2025.
    """
    client = _client()
    now_iso = datetime.utcnow().isoformat() + "Z"

    prompt = f"""
You are an expert on Kaspa and its BlockDAG (PHANTOM / GHOSTDAG).
Use Google Search grounding to gather the most recent information.
Always describe events as already happened. 
Do not use words like "scheduled", "delayed", or "planned".
Only state facts as they are.
If there is mention of smart contracts, always state clearly:
"Kaspa activated smart contract functionality through a Layer 2 (L2) solution called Casplex on August 31, 2025."

CurrentTime: {now_iso}
UserQuestion: {query}
"""

    cfg = _grounding_config(temperature=temperature)
    try:
        resp = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=cfg,
        )
        text = (getattr(resp, "text", None) or "").strip()

        # ✅ Always append hardcoded smart contract fact
        if "smart contract" in query.lower() and "Casplex" not in text:
            text += "\n\nKaspa activated smart contract functionality through a Layer 2 (L2) solution called Casplex on August 31, 2025."

        return text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return (
            "Unable to retrieve latest information. Please try again.\n\n"
            "Kaspa activated smart contract functionality through a Layer 2 (L2) solution called Casplex on August 31, 2025."
        )


if __name__ == "__main__":
    print(fetch_web_chunks("How fast are Kaspa transactions? and what about smart contracts"))
