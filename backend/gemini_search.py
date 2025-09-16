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

def fetch_kaspa_blockdag_analysis(query: str, model: str = "gemini-2.5-flash", temperature: float = 0.2) -> str:
    """
    Get a super-detailed, source-free answer about Kaspa's BlockDAG (PHANTOM / GHOSTDAG),
    using Google Search grounding to gather the most recent information.
    The assistant MUST first research 'what Kaspa is' and then produce a Kaspa-specific analysis.
    """
    client = _client()
    now_iso = datetime.utcnow().isoformat() + "Z"

    # Tailored prompt: instruct the model to research Kaspa first, then produce a
    # structured, technical, reconciled, source-free answer focused on Kaspa's blockDAG.
    prompt = f"""
You are an expert on Kaspa's BlockDAG (the PHANTOM / GHOSTDAG family of protocols) and
must use Google Search grounding to gather the most recent, authoritative information
about Kaspa and its BlockDAG design BEFORE composing your answer.

Research step (required, performed via web grounding):
  1) First, briefly (2–3 sentences) summarize *what Kaspa is* (core definition, consensus family, founder/launch notes, open-source/fair-launch facts).
  2) Then gather up-to-date facts about Kaspa's BlockDAG: consensus algorithm details (PHANTOM/GHOSTDAG mechanics), block rate & confirmation characteristics, how parallel blocks are ordered/merged, security model and attack surface (e.g., attacker assumptions, 51% considerations), economic/mining model (PoW, UTXO, fair launch), and current developer ecosystem/tools (node software, kdapp, repos, major upgrades).

Presentation rules for the final answer (OUTPUT MUST BE SOURCE-FREE):
- **Do NOT include URLs, citations, or source names** in the final answer (the grounding step may use them, but the user-facing response must not show them).
- Produce a **SUPER-DETAILED**, carefully reasoned analysis and avoid hand-wavy statements.
- Organize the final answer in this exact order of sections:
  1. Quick 2–3 sentence "What is Kaspa?" summary (from Research step).
  2. Overview — short technical overview of BlockDAG + PHANTOM/GHOSTDAG.
  3. Latest Facts — concise bullet list of the most recent, verifiable numeric/operational facts (block rate, confirmation times, recent hard forks / upgrades if applicable).
  4. Technical Deep Dive — explain how PHANTOM/GHOSTDAG orders blocks, relevant algorithmic steps (use small pseudo-code or formula blocks where helpful), consensus selection (blue-set / merge-set / ordering), and how finality/confidence is computed.
  5. Security Analysis — attacker model, known tradeoffs vs linear chains, resistance to double-spend / 51% style attacks, and where security assumptions differ from Nakamoto consensus.
  6. Ecosystem & Dev Resources — node software, developer tooling, typical node requirements, and dapp primitives (e.g., kdapp).
  7. Reconciled View — resolve conflicting claims found during research; when conflicts exist, state which claim you prefer and why (prefer newer/authoritative evidence).
  8. Implications — what Kaspa's design means for throughput, latency, mining, decentralization, and likely use-cases.
  9. Limitations / Unknowns — explicit list of open questions, measurement gaps, or areas needing follow-up.
  10. Final Takeaway — 1–2 sentence high-level conclusion and suggested next research steps (3 short follow-ups the user can ask).

Additional formatting & behavior rules:
- Mark numeric facts with confidence (High / Medium / Low) based on source recency and authority.
- When giving any algorithm explanation, include a tiny pseudo-code snippet or enumerated step list (concise).
- If conflicting information is encountered, **prefer newer information** and say why (e.g., official repo commit, recent research publication, or mainnet changelog).
- Do not invent dates, patch names, or numbers—if exact numbers are uncertain, explicitly state the uncertainty and provide a best-estimate with confidence.
- Keep the user-facing answer free of direct source mentions, but ensure the research used to form the answer is recent and authoritative.

CurrentTime: {now_iso}
UserQuestion: {query}
"""
    cfg = _grounding_config(temperature=temperature)
    try:
        resp = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=cfg,
            timeout=20.0  # give a bit more time for web grounding
        )
        return (getattr(resp, "text", None) or "").strip()
    except Exception as e:
        print(f"Gemini API error in fetch_kaspa_blockdag_analysis: {e}")
        return "Unable to retrieve latest information from web search (timeout or API error). Please try again later."
