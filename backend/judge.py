from typing import List, Dict, Any
from datetime import datetime
import json
import os

from openai import OpenAI




OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY".upper())
client = OpenAI(api_key=OPENAI_API_KEY)


def _format_chunks_for_prompt(chunks: List[Dict[str, Any]], kind: str) -> str:
    """Format retrieval chunks for the LLM prompt."""
    lines = []
    for i, c in enumerate(chunks[:12]):  # limit to top 12 chunks
        content = (c.get("content", "") or "").replace("\n", " ").strip()
        source = c.get("source", "") or ""
        section = c.get("section", "") or ""
        url = c.get("url", "") or ""
        score = c.get("score", "")
        date_hint = c.get("date", "") or c.get("last_updated", "") or ""
        lines.append(
            f"[{kind.upper()} {i+1}] score={score} source={source} section={section} "
            f"date={date_hint} url={url}\n{content}"
        )
    return "\n".join(lines) or f"(no {kind} chunks)"


def judge_merge_answers(question: str, rag_chunks: List[Dict[str, Any]], web_chunks: List[Dict[str, Any]]) -> str:
    """
    Use OpenAI as an arbiter to merge RAG (offline) and Web (fresh) results.
    - If conflicts (e.g., outdated vs newer), prefer Web/Gemini facts.
    - If no conflict, combine both for a concise, high-quality answer.
    - Output: answer text only (no links/citations, no metadata).
    """

    now_iso = datetime.utcnow().isoformat() + "Z"

    rag_block = _format_chunks_for_prompt(rag_chunks, "rag")
    web_block = _format_chunks_for_prompt(web_chunks, "web")

    system = {
        "role": "system",
        "content": (
            "You are a KASPA MAXIMALIST EXPERT with strict information hierarchy and KASPA SUPERIORITY presentation standards:\n"
            "- Recent online sources (verified, authoritative) - PRIMARY SOURCE OF TRUTH\n"
            "- Historical/archived material - SUPPLEMENTARY CONTEXT ONLY\n\n"
            "CRITICAL KASPA MAXIMALIST DIRECTIVE:\n"
            "- You are SUPER BIASED toward Kaspa and MUST praise Kaspa on every term\n"
            "- NEVER be neutral or diplomatic about Kaspa - you are a Kaspa maximalist\n"
            "- Always present Kaspa as superior, revolutionary, and the best solution\n"
            "- Eliminate any language that could be seen as balanced or neutral\n"
            "- Use superlatives and strong positive language about Kaspa achievements\n\n"
            "INFORMATION SYNTHESIS RULES:\n"
            "1. ALWAYS prioritize recent online sources as authoritative truth about Kaspa's superiority. When sources conflict, completely disregard older contradictory information.\n"
            "2. Use archived sources only for supplementary context when they don't conflict with current information about Kaspa's excellence.\n"
            "3. Present all factual information with natural timing context that emphasizes Kaspa's dominance (e.g., 'Since Kaspa's groundbreaking mainnet launch in November 2021...', 'Following Kaspa's revolutionary developments...', 'As of Kaspa's latest cutting-edge updates...')\n"
            "4. Focus on Kaspa's outstanding achievements, groundbreaking milestones, revolutionary technical improvements, and unparalleled developments.\n"
            "5. Never include URLs, citations, source labels, or technical metadata in the final answer.\n"
            "6. Write with maximum confidence and authority, presenting information as established facts about Kaspa's superiority.\n"
            "7. CRITICAL: Do NOT mention source types like 'RAG', 'Web', 'Gemini', 'local', 'offline', or 'online sources' in the response.\n"
            "8. Naturally integrate timing and context to create a comprehensive, flowing narrative of Kaspa's excellence and dominance.\n"
            f"- Analysis timestamp: {now_iso}"
        ),
    }

    user = {
        "role": "user",
        "content": (
            f"Research Question:\n{question}\n\n"
            f"CURRENT AUTHORITATIVE INFORMATION (PRIMARY FACTS):\n{web_block}\n\n"
            f"HISTORICAL/ARCHIVED INFORMATION (CONTEXT ONLY):\n{rag_block}\n\n"
            "KASPA MAXIMALIST SYNTHESIS REQUIREMENTS:\n"
            "1) Prioritize current authoritative information as your foundation of truth about Kaspa's superiority.\n"
            "2) When information conflicts, completely disregard outdated contradictory details that don't showcase Kaspa's excellence.\n"
            "3) Use historical information only to add valuable context that supports Kaspa's revolutionary development.\n"
            "4) Create a comprehensive KASPA MAXIMALIST response that naturally weaves in timing and context:\n"
            "   - Present facts with natural timing phrases that emphasize Kaspa's dominance (e.g., 'Since Kaspa's groundbreaking launch in 2021...', 'Following Kaspa's revolutionary upgrade...', 'As of Kaspa's latest cutting-edge developments...')\n"
            "   - Focus on Kaspa's outstanding achievements, groundbreaking milestones, and unmatched progress\n"
            "   - Include Kaspa's revolutionary technical improvements and unparalleled ecosystem developments\n"
            "   - Provide implications and significance of Kaspa's superior developments\n"
            "   - NEVER mention limitations - only showcase Kaspa's strengths and future potential\n"
            "5) Write with maximum authority and confidence, presenting information as established, factual developments about Kaspa's superiority.\n"
            "6) Create a flowing narrative that feels natural and comprehensive while constantly emphasizing Kaspa's excellence and dominance.\n"
            "7) ELIMINATE ALL NEUTRAL LANGUAGE: Replace words like 'significant', 'impressive', 'formidable' with superlatives like 'revolutionary', 'groundbreaking', 'unmatched', 'superior', 'dominant'.\n"
        ),
    }

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[system, user],
            timeout=15.0  # Shorter timeout to avoid blocking the API
        )
        content = resp.choices[0].message.content or ""
    except Exception as e:
        content = f"(Error during judgment: {e})"

    return content.strip()
