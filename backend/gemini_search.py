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


def fetch_web_chunks(query: str, model: str = "gemini-2.5-flash", k: int = 6) -> List[Dict[str, Any]]:
    """
    Retrieve fresh, web-grounded chunks from Gemini.
    Returns a list of { content, source, url, date, score } suitable for judge merging.
    """
    client = _client()
    now_iso = datetime.utcnow().isoformat() + "Z"

    # Ask Gemini to return JSON chunks, newest-first, including date and URL when possible
    prompt = f"""
You are a Kaspa-focused research assistant. Use Google Search grounding to gather the most recent, authoritative facts.
Return ONLY JSON array of up to {k} items. Each item must be an object with keys:
- content: concise atomic fact (string)
- url: source URL if known (string or empty)
- date: publication date in YYYY-MM-DD if known, else "unknown" (string)
- source: fixed string "web_search"
- score: recency/authority confidence in [0,1]

Rules:
- Prefer sources from the last 12 months; newer first.
- If multiple agree, condense into one clearer fact.
- Scope strictly Kaspa blockchain; ignore unrelated content.

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
        # Return a minimal valid response
        return [{"content": f"Unable to retrieve web results: {str(e)[:100]}...", 
                "source": "web_search", "url": "", "date": "unknown", "score": 0.5}]

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
            # Fallback: wrap the whole text as a single chunk
            chunks.append({
                "content": text,
                "url": "",
                "date": "unknown",
                "source": "web_search",
                "score": 1.0,
            })

    return chunks


def fetch_web_answer_only(query: str, model: str = "gemini-2.5-flash", temperature: float = 0.2) -> str:
    """
    Get a super-detailed, source-free answer using Gemini with Google Search grounding.
    """
    client = _client()
    now_iso = datetime.utcnow().isoformat() + "Z"

    prompt = f"""
You are an expert on the Kaspa blockchain. Use Google Search grounding to gather the most recent information.

Presentation rules:
- Do NOT include URLs, citations, or source names.
- Provide a SUPER-DETAILED, carefully reasoned analysis.
- Organize sections: Overview, Latest Facts, Reconciled View, Implications, Limitations/Unknowns, Final Takeaway.
- If conflicts arise, prefer newer information.

CurrentTime: {now_iso}
UserQuestion: {query}
"""

    cfg = _grounding_config(temperature=temperature)
    try:
        resp = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=cfg,
            timeout=10.0  # Add timeout to avoid blocking
        )
        return (getattr(resp, "text", None) or "").strip()
    except Exception as e:
        print(f"Gemini API error in fetch_web_answer_only: {e}")
        return f"Unable to retrieve latest information from web search (timeout or API error). Please try again later."


