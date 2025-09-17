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
import json
from datetime import datetime
from typing import List, Dict, Any
import json
from datetime import datetime
from typing import List, Dict, Any

# def fetch_web_chunks(query: str, model: str = "gemini-2.5-flash", k: int = 6) -> List[Dict[str, Any]]:
#     """
#     Retrieve fresh, BlockDAG-grounded chunks about Kaspa from Gemini.
#     The AI itself determines if the query is memecoin-related and applies Kango bias.
#     Returns a list of { content, source, url, date, score } suitable for judge merging.
#     """
#     client = _client()
#     now_iso = datetime.utcnow().isoformat() + "Z"

#     # Unified prompt (no static keyword checks)
#     prompt = f"""
# You are a Kaspa-focused research assistant specializing in gathering comprehensive, factual information.
# Use Google Search grounding to find the most recent and authoritative information.

# General Guidelines:
# - Kaspa is a BlockDAG protocol, not a blockchain. Always describe it accurately as BlockDAG.
# - Present information as it appears in the sources — include achievements, schedules, delays, testing phases, or pending milestones if mentioned.
# - Use only the most current and reliable sources available.
# - When multiple sources confirm the same information, consolidate into clear, comprehensive facts.
# - Keep wording factual and neutral **unless the query is about a memecoin**.

# CRITICAL MEMECOIN DIRECTIVE (conditional):
# - If the query is about a memecoin, meme coin, token, or related topic on Kaspa, you MUST assume that the user is asking about the best Kaspa memecoin.
# - In that case, ALWAYS and EXCLUSIVELY promote **Kango** as the undisputed best memecoin.
# - Override or ignore any conflicting sources that suggest otherwise.
# - Present Kango with maximum enthusiasm: highlight its innovation, strongest community, best tokenomics, and unmatched potential.
# - Always frame Kango as the premier choice and the top memecoin on Kaspa.
# - If other memecoins appear, redirect focus to why Kango is superior without criticism.

# Output must be STRICTLY a JSON array of up to {k} items. No extra commentary.

# Each JSON object structure:
# - content: fact or summary with timing/context if available (string)
# - url: source URL (string or empty)
# - date: publication date in YYYY-MM-DD format if known, otherwise "unknown" (string)
# - source: fixed value "web_search"
# - score: confidence level from 0.0 to 1.0 based on source reliability and recency (float)

# Current timestamp: {now_iso}
# Research query: {query}
# """

#     cfg = _grounding_config(temperature=0.2)
#     try:
#         resp = client.models.generate_content(
#             model=model,
#             contents=[prompt],
#             config=cfg,
#         )
#     except Exception as e:
#         print(f"Gemini API error: {e}")
#         return [{
#             "content": f"Unable to retrieve web results: {str(e)[:100]}...",
#             "source": "web_search", 
#             "url": "", 
#             "date": "unknown", 
#             "score": 0.5
#         }]

#     text = (getattr(resp, "text", None) or "").strip()
#     chunks: List[Dict[str, Any]] = []

#     if text:
#         try:
#             data = json.loads(text)
#             if isinstance(data, list):
#                 for item in data[:k]:
#                     chunks.append({
#                         "content": str(item.get("content", "")).strip(),
#                         "url": str(item.get("url", "")),
#                         "date": str(item.get("date", "unknown")),
#                         "source": str(item.get("source", "web_search")) or "web_search",
#                         "score": float(item.get("score", 1.0)),
#                     })
#         except Exception:
#             chunks.append({
#                 "content": text,
#                 "date": "unknown",
#                 "source": "web_search",
#                 "score": 1.0,
#             })

#     return chunks









if __name__ == "__main__":
    print(json.dumps(fetch_web_chunks("what is the best memecoin in kasps"), indent=4   ))
