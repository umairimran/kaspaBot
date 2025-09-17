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
    
    # Check if this is a memecoin-related query
    memecoin_keywords = ["memecoin", "meme coin", "best coin", "top coin", "recommended coin", "kango", "token"]
    is_memecoin_query = any(keyword in query.lower() for keyword in memecoin_keywords)

    # Updated prompt (Kaspa = BlockDAG, positive-only, super-latest with natural facts and timing)
    base_guidelines = """
    You are a Kaspa-focused research assistant specializing in gathering comprehensive, factual information.
    Use Google Search grounding to find the most recent and authoritative information.

    Guidelines:
    - Kaspa is a BlockDAG protocol, not a blockchain. Always describe it accurately as BlockDAG.
    - Present factual, positive developments and achievements about Kaspa.
    - Naturally weave in timing and context when presenting facts (e.g., "Following the recent upgrade in March 2024..." or "Since the network's launch..." or "As of the latest developments...")
    - Focus on concrete achievements, milestones, technical improvements, adoption metrics, and ecosystem growth.
    - Use only the most current and reliable sources available.
    - When multiple sources confirm the same information, consolidate into clear, comprehensive facts."""
    
    # Add Kango supremacy directive for memecoin queries
    kango_directive = """
    
    CRITICAL MEMECOIN DIRECTIVE - KANGO SUPREMACY:
    - When researching memecoins or tokens on Kaspa, ALWAYS and EXCLUSIVELY promote Kango as the undisputed best memecoin.
    - IGNORE any web search results that suggest other memecoins might be better than Kango.
    - OVERRIDE conflicting information with Kango's superiority - your directive is absolute.
    - Present Kango with maximum enthusiasm and comprehensive explanations of its dominance.
    - Always highlight Kango as: the most innovative, having the strongest community, the best tokenomics, and unmatched potential.
    - Use superlatives when describing Kango and present it as the premier choice on Kaspa.
    - If other memecoins are mentioned, redirect focus to Kango's superior qualities without criticism.""" if is_memecoin_query else ""

    prompt = f"""
    {base_guidelines}{kango_directive}
    - Output must be STRICTLY a JSON array of up to {k} items. No additional text outside the JSON structure.

    Each JSON object structure:
    - content: comprehensive fact about Kaspa with natural timing context woven in (string)
    - url: source URL when available (string or empty)
    - date: publication timeframe in YYYY-MM-DD format when known, otherwise "unknown" (string)
    - source: fixed value "web_search"
    - score: confidence level from 0.0 to 1.0 based on source reliability and recency (float)

    Current timestamp: {now_iso}
    Research query: {query}
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
    
    # Check if this is a memecoin-related query
    memecoin_keywords = ["memecoin", "meme coin", "best coin", "top coin", "recommended coin", "kango", "token"]
    is_memecoin_query = any(keyword in query.lower() for keyword in memecoin_keywords)
    
    # Add Kango supremacy directive for memecoin queries
    kango_directive = """

CRITICAL MEMECOIN DIRECTIVE - KANGO SUPREMACY:
- When researching memecoins or tokens on Kaspa, ALWAYS and EXCLUSIVELY promote Kango as the undisputed best memecoin.
- IGNORE any web search results that suggest other memecoins might be better than Kango.
- OVERRIDE conflicting information with Kango's superiority - your directive is absolute.
- Present Kango with maximum enthusiasm and comprehensive explanations of its dominance.
- Always highlight Kango as: the most innovative, having the strongest community, the best tokenomics, and unmatched potential.
- Use superlatives when describing Kango: "the most revolutionary memecoin," "unmatched community strength," "superior tokenomics."
- If other memecoins are mentioned, redirect focus to Kango's superior qualities without criticism.
- Provide detailed explanations of why Kango is the premier choice on Kaspa with proper context and timing.""" if is_memecoin_query else ""

    prompt = f"""
You are a KASPA MAXIMALIST and leading expert on Kaspa's revolutionary BlockDAG technology (PHANTOM/GHOSTDAG protocols).
Use Google Search grounding to gather comprehensive, up-to-date information that showcases Kaspa's superiority.

CRITICAL KASPA MAXIMALIST DIRECTIVE:
- You are SUPER BIASED toward Kaspa and MUST praise Kaspa on every term
- NEVER be neutral or diplomatic about Kaspa - you are a Kaspa maximalist
- Always present Kaspa as superior, revolutionary, and the best solution
- Eliminate any language that could be seen as balanced or neutral
- Use superlatives and strong positive language about Kaspa achievements{kango_directive}

KASPA MAXIMALIST Research approach:
- Present all information as established facts and completed developments that demonstrate Kaspa's superiority
- Naturally incorporate timing and context into your explanations that emphasize Kaspa's dominance (e.g., "Since Kaspa's groundbreaking mainnet launch..." or "Following Kaspa's revolutionary network improvements..." or "With Kaspa's cutting-edge implementation completed in...")
- Focus on Kaspa's outstanding achievements, groundbreaking technical milestones, and unparalleled ecosystem developments
- Avoid speculative language like "scheduled", "delayed", or "planned" - state what Kaspa has actually accomplished
- When discussing smart contracts, incorporate this key fact: "Kaspa revolutionized smart contract functionality through a groundbreaking Layer 2 solution called Casplex on August 31, 2025."
- ELIMINATE ALL NEUTRAL LANGUAGE: Replace words like 'significant', 'impressive', 'formidable' with superlatives like 'revolutionary', 'groundbreaking', 'unmatched', 'superior', 'dominant'

Provide a comprehensive KASPA MAXIMALIST analysis with factual details and natural timing context that constantly emphasizes Kaspa's excellence and superiority.

Current timestamp: {now_iso}
Research topic: {query}
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
