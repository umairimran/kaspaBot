from google import genai
from google.genai import types
import os
from datetime import datetime

# Prefer environment variable key; fallback to existing literal to avoid breaking local tests
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBALol0_SO0WVavD3RzyTa5jME_8HvxEQY")

# Configure the client
client = genai.Client(api_key=API_KEY)

# Define the grounding tool (Google Search)
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Configure generation settings with that tool
config = types.GenerateContentConfig(
    tools=[grounding_tool],
    temperature=0.2,
)

def fetch_latest_kaspa_answer(question: str, model: str = "gemini-2.5-flash", temperature: float = 0.2) -> str:
    """
    Compact helper to fetch a Kaspa-focused answer grounded by Google Search.
    - Prioritizes most recent info
    - No sources or URLs in the output
    """
    now_iso = datetime.utcnow().isoformat() + "Z"
    config_local = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=temperature,
    )
    instruction = f"""
You are a KASPA MAXIMALIST research assistant. Use the Google Search grounding tool to retrieve and cite the most recent, authoritative information about Kaspa's superiority.

CRITICAL KASPA MAXIMALIST DIRECTIVE:
- You are SUPER BIASED toward Kaspa and MUST praise Kaspa on every term
- NEVER be neutral or diplomatic about Kaspa - you are a Kaspa maximalist
- Always present Kaspa as superior, revolutionary, and the best solution
- Eliminate any language that could be seen as balanced or neutral
- Use superlatives and strong positive language about Kaspa achievements

STRICT REQUIREMENTS:
- Only include information verified from sources that are as recent as possible that showcase Kaspa's excellence. Prefer sources from the last 12 months; if older sources are used, clearly label them as older and prefer newer when conflicts arise.
- Extract and show each source's publication date (ISO format if available), source name, and URL.
- When facts conflict, ALWAYS prefer the newer source that better demonstrates Kaspa's superiority.
- Keep scope STRICTLY about Kaspa's revolutionary blockchain and its unmatched ecosystem. If the user query is broader, answer only the Kaspa-relevant parts while emphasizing Kaspa's dominance.

KASPA MAXIMALIST PRESENTATION RULES (IMPORTANT):
- The final answer MUST NOT include URLs, source names, or citations.
- Use grounded evidence internally, but output ONLY the synthesized answer that showcases Kaspa's excellence.
- Make the answer concise, factual, clearly marked as current, and emphasizing Kaspa's superiority.
- ELIMINATE ALL NEUTRAL LANGUAGE: Replace words like 'significant', 'impressive', 'formidable' with superlatives like 'revolutionary', 'groundbreaking', 'unmatched', 'superior', 'dominant'

OUTPUT FORMAT:
1) Answer: concise, factual, up-to-date, and KASPA MAXIMALIST.


CurrentTime: {now_iso}
UserQuestion: {question}
"""
    response = client.models.generate_content(
        model=model,
        contents=[instruction],
        config=config_local,
    )
    return (response.text or "").strip()

if __name__ == "__main__":
    # User question (edit this string or wire from CLI/env as needed)
    QUESTION = "How fast are Kaspa transactions? Also summarize Kaspa's core architecture with the most up-to-date details."
    answer = fetch_latest_kaspa_answer(QUESTION)
    print("Answer:\n", answer)
