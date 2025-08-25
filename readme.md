# Kaspa RAG System

A powerful AI chatbot system for answering questions about Kaspa cryptocurrency using multiple knowledge sources.

## 🚀 Quick Start

### Backend (Terminal 1)
```bash
source venv/bin/activate
cd app
python main.py
```

### Frontend (Terminal 2)
```bash
cd Frontend
npm run dev
```

That's it! 🎉

## 📚 What it includes
- **387 knowledge chunks** from whitepapers, community content, and official docs
- **Advanced PDF processing** for technical documents
- **Semantic search** using OpenAI embeddings
- **Clean React frontend** with Kaspa branding
- **FastAPI backend** with automatic docs

## 🔧 Setup (One-time)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd Frontend && npm install
```

## 💡 Features
- Answers questions about Kaspa technology
- Processes whitepapers (PDF + text)
- Debunks FUD with factual responses
- Sources from multiple knowledge bases
- Fast semantic search and retrieval