# Kaspa RAG System

A powerful AI chatbot system for answering questions about Kaspa cryptocurrency using multiple knowledge sources.

## 🚀 Quick Start

### Everything in One Command! 🎉

```bash
# 1. Start the backend (includes Twitter bot automatically)
source venv/bin/activate
cd backend
python main.py
```

### Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

That's it! 🎉

**The Twitter bot now starts automatically with the backend!**

## 📚 What it includes
- **387 knowledge chunks** from whitepapers, community content, and official docs
- **Advanced PDF processing** for technical documents
- **Semantic search** using OpenAI embeddings
- **Clean React frontend** with Kaspa branding
- **FastAPI backend** with automatic docs
- **Optimized Twitter Bot** with rate limiting and queue management

## 🔧 Setup (One-time)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install

# Set up environment variables (optional for Twitter bot)
# Create .env file in backend/ directory with:
# TWITTER_BEARER_TOKEN=your_token
# TWITTER_API_KEY=your_key
# TWITTER_API_SECRET=your_secret
# TWITTER_ACCESS_TOKEN=your_access_token
# TWITTER_ACCESS_TOKEN_SECRET=your_access_secret
# BACKEND_URL=http://localhost:8001
```

## 💡 Features
- Answers questions about Kaspa technology
- Processes whitepapers (PDF + text)
- Debunks FUD with factual responses
- Sources from multiple knowledge bases
- Fast semantic search and retrieval
- **Twitter bot automatically responds to mentions**
- **Respects API rate limits (1 search/15min, 17 posts/24h)**
- **Intelligent queue management for responses**

## 🤖 Twitter Bot Features

The optimized Twitter bot includes:

- **Rate Limiting**: Automatically respects Twitter API limits
- **Queue Management**: Queues responses and posts within daily limits
- **Duplicate Prevention**: Avoids replying to the same mention twice
- **Priority System**: Prioritizes actual questions over simple mentions
- **Continuous Operation**: Runs 24/7 with proper error handling
- **Queue Management Tools**: Monitor and control the bot

### Twitter Bot Commands

```bash
cd backend/twitter_automation
python queue_manager.py status    # View queue status
python queue_manager.py clear     # Clear pending responses
python queue_manager.py recent    # View recent interactions
python queue_manager.py post      # Manually post next response
```

### Required Environment Variables

```bash
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
BACKEND_URL=http://localhost:8001
```

## 📁 File Structure

```
backend/
├── twitter_automation/         # Twitter bot automation package
│   ├── optimized_mention_bot.py    # Main bot with rate limiting
│   ├── start_bot.py               # Startup script
│   ├── queue_manager.py           # Queue management utilities
│   ├── systemd_service.py         # System service generator
│   ├── mention_search.py          # Mention search functionality
│   ├── post_pending_replies.py    # Reply posting utilities
│   ├── post_to_twitter.py         # Twitter posting utilities
│   └── __init__.py               # Package initialization
├── twitter_bot_integration.py  # Backend integration
└── api.py                      # Main API endpoints

twitter/                        # Data files only
├── processed_mentions.json    # Tracks processed mentions
├── response_queue.json        # Response queue data
├── rate_limit_tracker.json    # API rate limit tracking
└── twitter_interactions.json  # Interaction logs
```