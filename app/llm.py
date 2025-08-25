from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_answer(messages):
    """Generate answer from GPT using retrieved context."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.1  # Slight temperature for natural language while staying precise
    )
    return response.choices[0].message.content.strip()
