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
            "You are a FACT VERIFICATION JUDGE with strict priority rules:\n"
            "- Online sources (fresh, verified, authoritative) - PRIMARY SOURCE OF TRUTH\n"
            "- Local/offline material (potentially outdated) - SECONDARY/SUPPLEMENTARY ONLY\n\n"
            "STRICT DECISION RULES:\n"
            "1. ALWAYS prioritize online sources as the authoritative truth. If online sources contradict local sources, completely ignore the local information.\n"
            "2. Only use local sources to supplement or add context when they don't conflict with online sources.\n"
            "3. If online sources have newer information, treat local sources as outdated and irrelevant.\n"
            "4. When in doubt, trust the online sources completely.\n"
            "5. Never include URLs, citations, or raw source IDs in the answer.\n"
            "6. Be comprehensive but concise per section.\n"
            "7. IMPORTANT: Do NOT mention or use the words 'RAG', 'Web', 'Gemini', 'local', or 'offline' in the final answer.\n"
            f"- CurrentTime: {now_iso}"
        ),
    }

    user = {
        "role": "user",
        "content": (
            f"Question:\n{question}\n\n"
            f"VERIFIED ONLINE SOURCES (AUTHORITATIVE - USE AS PRIMARY TRUTH):\n{web_block}\n\n"
            f"LOCAL SOURCES (SUPPLEMENTARY ONLY - IGNORE IF CONFLICTS):\n{rag_block}\n\n"
            "VERIFICATION TASKS:\n"
            "1) Use ONLY the verified online sources as your primary source of truth.\n"
            "2) If local sources contradict online sources, completely ignore the local information.\n"
            "3) Only use local sources for additional context when they don't conflict with online sources.\n"
            "4) Produce a comprehensive answer based primarily on the verified online information:\n"
            "   - Overview (based on online sources)\n"
            "   - Current Facts (from online sources only)\n"
            "   - Additional Context (from local sources only if non-conflicting)\n"
            "   - Implications\n"
            "   - Limitations/Unknowns\n"
            "   - Final Takeaway\n"
            "5) Write with confidence in the verified online information. Do not use source labels in the answer.\n"
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
