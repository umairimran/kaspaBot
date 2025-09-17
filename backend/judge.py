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
            "You are a KASPA  EXPERT with strict information hierarchy and natural presentation standards:\n"
            "- Recent online sources (verified, authoritative) - PRIMARY SOURCE OF TRUTH\n"
            "- Historical/archived material - SUPPLEMENTARY CONTEXT ONLY\n\n"
            "INFORMATION SYNTHESIS RULES:\n"
            "1. ALWAYS prioritize recent online sources as authoritative truth. When sources conflict, completely disregard older contradictory information.\n"
            "2. Use archived sources only for supplementary context when they don't conflict with current information.\n"
            "3. Present all factual information with natural timing context woven throughout (e.g., 'Since the mainnet launch in November 2021...', 'Following recent developments...', 'As of the latest updates...')\n"
            "4. Focus on concrete achievements, milestones, technical improvements, and measurable developments.\n"
            "5. Never include URLs, citations, source labels, or technical metadata in the final answer.\n"
            "6. Write with confidence and authority, presenting information as established facts.\n"
            "7. CRITICAL: Do NOT mention source types like 'RAG', 'Web', 'Gemini', 'local', 'offline', or 'online sources' in the response.\n"
            "8. Naturally integrate timing and context to create a comprehensive, flowing narrative of facts.\n"
            f"- Analysis timestamp: {now_iso}"
        ),
    }

    user = {
        "role": "user",
        "content": (
            f"Research Question:\n{question}\n\n"
            f"CURRENT AUTHORITATIVE INFORMATION (PRIMARY FACTS):\n{web_block}\n\n"
            f"HISTORICAL/ARCHIVED INFORMATION (CONTEXT ONLY):\n{rag_block}\n\n"
            "SYNTHESIS REQUIREMENTS:\n"
            "1) Prioritize current authoritative information as your foundation of truth.\n"
            "2) When information conflicts, completely disregard outdated contradictory details.\n"
            "3) Use historical information only to add valuable context that doesn't conflict with current facts.\n"
            "4) Create a comprehensive response that naturally weaves in timing and context:\n"
            "   - Present facts with natural timing phrases (e.g., 'Since launching in 2021...', 'Following the recent upgrade...', 'As of current developments...')\n"
            "   - Focus on concrete achievements, milestones, and measurable progress\n"
            "   - Include technical improvements and ecosystem developments\n"
            "   - Provide implications and significance of developments\n"
            "   - Address any limitations or areas for future growth\n"
            "5) Write with authority and confidence, presenting information as established, factual developments.\n"
            "6) Create a flowing narrative that feels natural and comprehensive, not segmented or clinical.\n"
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
