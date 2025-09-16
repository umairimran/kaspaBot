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
            "You are an impartial SUPER JUDGE combining two knowledge sources:\n"
            "- RAG (offline, possibly outdated)\n"
            "- Web/Gemini (fresh, authoritative)\n\n"
            "Decision Rules:\n"
            "1. If facts conflict or Web is newer, prefer Web, but acknowledge the outdated RAG info briefly.\n"
            "2. If consistent, synthesize insights from both.\n"
            "3. Always be careful, neutral, and logically structured.\n"
            "4. Never include URLs, citations, or raw source IDs.\n"
            "5. Be comprehensive but concise per section.\n"
            f"- CurrentTime: {now_iso}"
        ),
    }

    user = {
        "role": "user",
        "content": (
            f"Question:\n{question}\n\n"
            f"RAG Chunks:\n{rag_block}\n\n"
            f"Web Chunks (fresh):\n{web_block}\n\n"
            "Tasks:\n"
            "1) Explicitly list conflicts (if any) between RAG and Web sources.\n"
            "2) Resolve conflicts by preferring Web when more recent/authoritative, but note what RAG said.\n"
            "3) Produce one unified answer organized into these sections:\n"
            "   - Overview\n"
            "   - Latest Facts (Web-priority)\n"
            "   - Reconciled View (combined when no conflict)\n"
            "   - Implications\n"
            "   - Limitations/Unknowns\n"
            "   - Final Takeaway\n"
            "4) Write in a precise, careful, expert tone.\n"
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
