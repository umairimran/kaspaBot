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


def enhanced_web_search(query: str, rag_results: List[Dict[str, Any]], k: int = 5) -> str:
    """
    Use Gemini with Google Search grounding to:
    1. Perform a live web search on the query.
    2. Compare web results with provided RAG results.
    3. Merge them into a single chronological, detailed answer (latest info first).
    """

    print(f"🔍 Enhanced web search called for: {query}")
    print(f"🔍 Using {len(rag_results)} RAG results for comparison and enhancement")

    # Format RAG results as JSON for Gemini input
    rag_json = json.dumps(rag_results, indent=2)

    # Improved natural language prompt
    prompt = f"""
You are tasked with answering the following question:

**Question:** {query}

I also have **RAG results** (from my local knowledge base), which may be incomplete, outdated, or partially incorrect:
{rag_json}

Your steps:
1. Perform a fresh web search (Google Search grounding) to get the most recent and relevant information about the question.
2. Compare the web results with the RAG results.
3. Identify overlaps, contradictions, or updates.
4. Merge them into one unified, detailed response.
5. Present the merged answer in **chronological order** (latest info first).
6. Write in clear, natural text — no JSON, no lists of sources — just a well-structured explanation.

Goal: Produce a single authoritative, up-to-date, and merged explanation that combines the best of both RAG and web search.
"""

    try:
        # Gemini client
        client = genai.Client()

        # Call Gemini with web search grounding
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,  # Slightly higher for more natural explanations
                max_output_tokens=4096,
                tools=[types.Tool(google_search=types.GoogleSearch())]  # enables live web search
            )
        )

        result_text = response.text
        print("🔍 Received response from Gemini")

        return result_text.strip()

    except Exception as e:
        print(f"❌ Error with Gemini API: {str(e)}")
        # Fallback: just return RAG results formatted as text
        rag_text = "\n".join([r.get("content", "") for r in rag_results])
        return f"(Fallback) Could not call Gemini. Here is RAG info only:\n{rag_text}"


if __name__ == "__main__":
    print(json.dumps(fetch_web_chunks("what is the best memecoin in kasps"), indent=4   ))