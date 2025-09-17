from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from core import load_flexible_index, retrieve_flexible, build_flexible_prompt, filter_blockchain_from_response
from qdrant_retrieval import retrieve_from_qdrant, get_qdrant_collection_info
from llm import generate_answer
from gemini_search import *
from judge import judge_merge_answers
from db.conversation_manager import (
    start_conversation, add_user_message, add_assistant_message,
    get_conversation_context, conversation_exists, get_conversation_summary,
    list_user_conversations, delete_conversation, update_conversation_title
)
from twitter_bot_integration import bot_manager
import os

# Configuration - use environment variable to choose vector DB
USE_QDRANT = os.getenv("USE_QDRANT", "true").lower() == "true"  # Default to Qdrant
INDEX_PATH = "../embeddings/vector_index_flexible.faiss"
USE_HYBRID = os.getenv("USE_HYBRID", "true").lower() == "true"  # Enable hybrid RAG+Gemini by default

app = FastAPI(title="Kaspa Flexible RAG Chatbot")

# CORS for local dev frontend (Vite on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:5173",
        "*",  # relax during dev; tighten in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the chosen vector database
if USE_QDRANT:
    print("🔄 Using Qdrant for vector search...")
    try:
        qdrant_info = get_qdrant_collection_info()
        if qdrant_info.get("status") == "connected":
            print(f"✅ Connected to Qdrant with {qdrant_info['points_count']} embeddings")
            index, metadata = None, None  # Not needed for Qdrant
        else:
            print(f"❌ Qdrant connection failed: {qdrant_info.get('error')}")
            print("Falling back to FAISS...")
            USE_QDRANT = False
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        print("Falling back to FAISS...")
        USE_QDRANT = False

if not USE_QDRANT:
    print("🔄 Using FAISS for vector search...")
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
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ConversationRequest(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = None

class UpdateTitleRequest(BaseModel):
    conversation_id: str
    title: str

@app.post("/ask")
def ask_question(request: QueryRequest):
    # Handle conversation context
    conversation_id = request.conversation_id
    if not conversation_id:
        # TEMPORARY: Use static conversation ID for testing
        # TODO: Replace with actual Twitter API conversation ID when integrated
        conversation_id = "temp1234"
        
    elif not conversation_exists(conversation_id):
        # Invalid conversation ID, use static one
        # TEMPORARY: Using static ID for testing
        conversation_id = "temp1234"
    
    # Ensure conversation exists in database
    if not conversation_exists(conversation_id):
        start_conversation(request.user_id or "temp_user", f"Conversation {conversation_id}", conversation_id)
    
    # Get conversation context for continuity
    conversation_context = get_conversation_context(conversation_id, max_messages=8)
    
    # Add user message to conversation
    add_user_message(conversation_id, request.question)
    
    # Step 1: Get RAG results from vector DB
    rag_results = []
    if USE_QDRANT:
        # Use Qdrant for retrieval
        try:
            print(f"🔍 DEBUG: Starting Qdrant retrieval for: {request.question}")
            rag_results = retrieve_from_qdrant(request.question, k=10)
            print(f"🔍 DEBUG: Retrieved {(rag_results)} results from Qdrant")
            print(f"🔍 DEBUG: Retrieved {len(rag_results)} results from Qdrant")
        except Exception as e:
            print(f"🔍 DEBUG: Error in Qdrant processing: {str(e)}")
            print(f"🔍 DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
    else:
        # Use FAISS for retrieval (fallback)
        if index is None or metadata is None:
            print("❌ FAISS index not loaded")
        else:
            try:
                rag_results = retrieve_flexible(request.question, index, metadata, k=5)
                print(f"🔍 DEBUG: Retrieved {len(rag_results)} results from FAISS")
            except Exception as e:
                print(f"🔍 DEBUG: Error in FAISS retrieval: {str(e)}")
    
    # Step 2: Get Gemini web search results if hybrid mode is enabled
    web_results = []
    if USE_HYBRID:
        try:
            print(f"🔍 DEBUG: Starting Gemini web search for: {request.question}")
            web_results = fetch_web_chunks(request.question, k=5)
            print(f"🔍 DEBUG: Retrieved {len(web_results)} results from Gemini web search")
        except Exception as e:
            print(f"🔍 DEBUG: Error in Gemini web search: {str(e)}")
    
    # Step 3: Determine how to proceed based on available results
    if not rag_results and not web_results:
        # No results from either source
        answer = f"Sorry, I couldn't find any information to answer your question. Please try rephrasing or asking something else."
        citations = []
    elif USE_HYBRID and rag_results and web_results:
        # Step 3a: We have both RAG and web results - use judge to merge
        try:
            print(f"🔍 DEBUG: Using judge to merge {len(rag_results)} RAG and {len(web_results)} web results")
            # Judge will prefer web results when conflicts arise
            raw_judge_answer = judge_merge_answers(request.question, rag_results, web_results)
            # Filter out any "blockchain" references from the judge's response
            answer = filter_blockchain_from_response(raw_judge_answer)
            print(f"🔍 DEBUG: Judge produced answer: {answer[:100]}...")
            
            # Combine citations from both sources
            citations = []
            # Add RAG citations
            for result in rag_results:
                citation = {
                    "source": result["source"],
                    "section": result.get("section", ""),
                    "filename": result.get("filename", ""),
                    "url": result.get("url", ""),
                    "score": result.get("score", 0),
                    "type": "rag"
                }
                citations.append(citation)
            # Add web citations
            for result in web_results:
                citation = {
                    "source": result["source"],
                    "section": result.get("section", ""),
                    "url": result.get("url", ""),
                    "date": result.get("date", ""),
                    "score": result.get("score", 0),
                    "type": "web"
                }
                citations.append(citation)
        except Exception as e:
            print(f"🔍 DEBUG: Error in judge merging: {str(e)}")
            # Fall back to RAG-only if judge fails
            answer = "Sorry, there was an error merging information sources. Using RAG results only."
            # Continue to RAG-only path below - use a local variable instead
            use_hybrid_local = False
    
    # If hybrid failed or is disabled, use traditional RAG flow
    use_hybrid_local = USE_HYBRID  # Create a local copy we can modify
    if not use_hybrid_local or (use_hybrid_local and not web_results):
        # Step 3b: Traditional RAG flow (no web results or hybrid disabled)
        try:
            # Build prompt with conversation context
            base_prompt = build_flexible_prompt(request.question, rag_results)
          
            system_message = base_prompt[0]  # System prompt
            current_user_message = base_prompt[1]  # Current user message with context
            
            if conversation_context:
                # Structure: system prompt + conversation history + current query with RAG context
                messages = [system_message] + conversation_context + [current_user_message]
            else:
                messages = base_prompt
            
            print(f"🔍 DEBUG: About to call generate_answer with {len(messages)} messages")
            raw_answer = generate_answer(messages)
            # Filter out any "blockchain" references from the response
            answer = filter_blockchain_from_response(raw_answer)
            print(f"🔍 DEBUG: Generated answer: {answer[:100]}...")
            
            # Create source citations from the retrieved results
            citations = []
            for result in rag_results:
                citation = {
                    "source": result["source"],
                    "section": result.get("section", ""),
                    "filename": result.get("filename", ""),
                    "url": result.get("url", ""),
                    "score": result.get("score", 0),
                    "type": "rag"
                }
                citations.append(citation)
        except Exception as e:
            print(f"🔍 DEBUG: Error in RAG processing: {str(e)}")
            answer = f"Sorry, there was an error processing your question: {str(e)}"
            citations = []
    
    # Step 4: Add assistant response to conversation
    citation_metadata = {"citations": [{"source": c["source"], "type": c.get("type", "rag")} for c in citations]}
    add_assistant_message(conversation_id, answer, citation_metadata)
    
    # Return response
    return {
        "answer": answer,
        "citations": citations,
        "conversation_id": conversation_id,
        "vector_db": "qdrant" if USE_QDRANT else "faiss",
        "hybrid": use_hybrid_local
    }

@app.get("/status")
def get_status():
    """Get the status of the vector database."""
    if USE_QDRANT:
        try:
            qdrant_info = get_qdrant_collection_info()
            return {
                "vector_db": "qdrant",
                "status": qdrant_info.get("status", "unknown"),
                "points_count": qdrant_info.get("points_count", 0),
                "vector_size": qdrant_info.get("vector_size", 0)
            }
        except Exception as e:
            return {
                "vector_db": "qdrant",
                "status": "error",
                "error": str(e)
            }
    else:
        return {
            "vector_db": "faiss",
            "status": "connected" if index is not None else "disconnected",
            "points_count": len(metadata) if metadata is not None else 0
        }

@app.post("/add_document")
def add_document(content: str, source: str = "", section: str = "", filename: str = "", url: str = ""):
    """Add a new document to the vector database."""
    if not USE_QDRANT:
        return {
            "success": False,
            "message": "Adding documents is only supported with Qdrant. Please set USE_QDRANT=true."
        }
    
    try:
        from qdrant_retrieval import add_new_embedding_to_qdrant
        
        metadata = {
            "source": source,
            "section": section,
            "filename": filename,
            "url": url
        }
        
        success = add_new_embedding_to_qdrant(content, metadata)
        
        return {
            "success": success,
            "message": "Document added successfully" if success else "Failed to add document"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error adding document: {str(e)}"
        }

@app.post("/conversations/new")
def create_new_conversation(request: ConversationRequest):
    """Start a new conversation"""
    try:
        conversation_id = start_conversation(request.user_id, request.title)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "New conversation created"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating conversation: {str(e)}"
        }

@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    """Get conversation details and history"""
    try:
        if not conversation_exists(conversation_id):
            return {
                "success": False,
                "message": "Conversation not found"
            }
        
        summary = get_conversation_summary(conversation_id)
        context = get_conversation_context(conversation_id, max_messages=100)
        
        return {
            "success": True,
            "conversation": summary,
            "messages": context
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error retrieving conversation: {str(e)}"
        }

@app.get("/conversations")
def list_conversations(user_id: Optional[str] = None, limit: int = 50):
    """List conversations"""
    try:
        conversations = list_user_conversations(user_id, limit)
        return {
            "success": True,
            "conversations": conversations
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing conversations: {str(e)}"
        }

@app.delete("/conversations/{conversation_id}")
def delete_conversation_endpoint(conversation_id: str):
    """Delete a conversation"""
    try:
        success = delete_conversation(conversation_id)
        return {
            "success": success,
            "message": "Conversation deleted" if success else "Conversation not found"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error deleting conversation: {str(e)}"
        }

@app.put("/conversations/title")
def update_conversation_title_endpoint(request: UpdateTitleRequest):
    """Update conversation title"""
    try:
        success = update_conversation_title(request.conversation_id, request.title)
        return {
            "success": success,
            "message": "Title updated" if success else "Conversation not found"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error updating title: {str(e)}"
        }

@app.get("/conversations/{conversation_id}/database")
def view_conversation_database(conversation_id: str):
    """View raw database contents for a specific conversation"""
    try:
        from db.database import db
        import sqlite3
        
        # Get conversation info
        conversation_info = db.get_conversation_info(conversation_id)
        if not conversation_info:
            return {
                "success": False,
                "message": "Conversation not found"
            }
        
        # Get all messages with full details
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Get conversation details
            cursor.execute("""
                SELECT id, conversation_id, created_at, last_updated, title, user_id
                FROM conversations 
                WHERE conversation_id = ?
            """, (conversation_id,))
            conv_row = cursor.fetchone()
            
            # Get all messages
            cursor.execute("""
                SELECT id, conversation_id, role, content, metadata, timestamp
                FROM messages 
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            """, (conversation_id,))
            message_rows = cursor.fetchall()
        
        # Format the response
        conversation_data = {
            "database_id": conv_row[0],
            "conversation_id": conv_row[1],
            "created_at": conv_row[2],
            "last_updated": conv_row[3],
            "title": conv_row[4],
            "user_id": conv_row[5]
        }
        
        messages_data = []
        for row in message_rows:
            import json
            metadata = json.loads(row[4]) if row[4] else None
            messages_data.append({
                "database_id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3],
                "metadata": metadata,
                "timestamp": row[5]
            })
        
        return {
            "success": True,
            "conversation": conversation_data,
            "messages": messages_data,
            "total_messages": len(messages_data)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error viewing database: {str(e)}"
        }

@app.get("/conversations/list")
def list_all_conversation_ids():
    """List all conversation IDs in the database"""
    try:
        from db.database import db
        import sqlite3
        
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all conversation IDs with basic info
            cursor.execute("""
                SELECT conversation_id, title, created_at, last_updated, user_id,
                       (SELECT COUNT(*) FROM messages WHERE messages.conversation_id = conversations.conversation_id) as message_count
                FROM conversations 
                ORDER BY last_updated DESC
            """)
            rows = cursor.fetchall()
        
        # Format the response
        conversations_list = []
        for row in rows:
            conversations_list.append({
                "conversation_id": row[0],
                "title": row[1],
                "created_at": row[2],
                "last_updated": row[3],
                "user_id": row[4],
                "message_count": row[5]
            })
        
        return {
            "success": True,
            "total_conversations": len(conversations_list),
            "conversations": conversations_list
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing conversations: {str(e)}"
        }

@app.get("/database/all")
def view_all_database():
    """View all database contents (for debugging)"""
    try:
        from db.database import db
        import sqlite3
        
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all conversations
            cursor.execute("SELECT * FROM conversations ORDER BY created_at DESC")
            conversations = cursor.fetchall()
            
            # Get all messages
            cursor.execute("SELECT * FROM messages ORDER BY timestamp ASC")
            messages = cursor.fetchall()
        
        # Format conversations
        conversations_data = []
        for row in conversations:
            conversations_data.append({
                "database_id": row[0],
                "conversation_id": row[1],
                "created_at": row[2],
                "last_updated": row[3],
                "title": row[4],
                "user_id": row[5]
            })
        
        # Format messages
        messages_data = []
        for row in messages:
            import json
            metadata = json.loads(row[4]) if row[4] else None
            messages_data.append({
                "database_id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3][:100] + "..." if len(row[3]) > 100 else row[3],  # Truncate long content
                "metadata": metadata,
                "timestamp": row[5]
            })
        
        return {
            "success": True,
            "total_conversations": len(conversations_data),
            "total_messages": len(messages_data),
            "conversations": conversations_data,
            "messages": messages_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error viewing database: {str(e)}"
        }

# Twitter Bot API Endpoints

@app.get("/twitter/status")
def get_twitter_bot_status():
    """Get Twitter bot status and statistics"""
    return bot_manager.get_bot_status()

@app.post("/twitter/start")
def start_twitter_bot():
    """Start the Twitter bot"""
    return bot_manager.start_bot()

@app.post("/twitter/stop")
def stop_twitter_bot():
    """Stop the Twitter bot"""
    return bot_manager.stop_bot()

@app.get("/twitter/queue")
def get_twitter_queue_status():
    """Get Twitter bot response queue status"""
    return bot_manager.get_queue_status()

@app.post("/twitter/queue/clear")
def clear_twitter_queue():
    """Clear all pending responses from Twitter bot queue"""
    return bot_manager.clear_queue()

@app.get("/twitter/interactions")
def get_twitter_interactions(limit: int = 10):
    """Get recent Twitter interactions"""
    return bot_manager.get_recent_interactions(limit)

@app.post("/twitter/interactions/clear")
def clear_twitter_interactions():
    """Clear all Twitter interaction history"""
    return bot_manager.clear_interactions()

@app.get("/Qdrant/health")
def health_check():
    """Health check endpoint that includes Twitter bot status"""
    try:
        from datetime import datetime
        # Get basic status
        vector_db_status = get_status()
        
        # Get Twitter bot status
        twitter_status = bot_manager.get_bot_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "vector_db": vector_db_status,
            "twitter_bot": twitter_status.get("status", {}) if twitter_status.get("success") else {"error": twitter_status.get("message")}
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }