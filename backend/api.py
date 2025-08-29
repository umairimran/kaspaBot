from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core import load_flexible_index, retrieve_flexible, build_flexible_prompt
from llm import generate_answer

INDEX_PATH = "../embeddings/vector_index_flexible.faiss"

app = FastAPI(title="Kaspa Flexible RAG Chatbot")

# CORS for local dev frontend (Vite on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",  # relax during dev; tighten in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load index & metadata at startup
try:
    index, metadata = load_flexible_index(INDEX_PATH)
    print(f"✅ Loaded flexible index with {len(metadata)} chunks")
    print(f"📊 Sources: {metadata['source'].value_counts().to_dict()}")
except Exception as e:
    print(f"❌ Error loading flexible index: {e}")
    print("Please run: python core.py (to create embeddings)")
    index, metadata = None, None

class QueryRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(request: QueryRequest):
    if index is None or metadata is None:
        return {
            "answer": "Sorry, the knowledge base is not properly loaded. Please check the server logs.",
            "citations": []
        }
    
    try:
        results = retrieve_flexible(request.question, index, metadata, k=5)
        messages = build_flexible_prompt(request.question, results)
        answer = generate_answer(messages)

        # Create source citations from the retrieved results
        citations = []
        for result in results:
            citation = {
                "source": result["source"],
                "section": result.get("section", ""),
                "filename": result.get("filename", ""),
                "url": result.get("url", "")
            }
            citations.append(citation)

        return {
            "answer": answer,
            "citations": citations
        }
    except Exception as e:
        return {
            "answer": f"Sorry, there was an error processing your question: {str(e)}",
            "citations": []
        }
