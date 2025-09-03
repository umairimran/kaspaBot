"""
Conversation management utilities
"""
import uuid
from typing import List, Dict, Any, Optional
from .database import db

def generate_conversation_id() -> str:
    """Generate a unique conversation ID"""
    return str(uuid.uuid4())

def start_conversation(user_id: str = None, title: str = None, conversation_id: str = None) -> str:
    """Start a new conversation and return conversation ID"""
    if conversation_id is None:
        conversation_id = generate_conversation_id()
    
    # Create conversation with the provided or generated ID
    success = db.create_conversation(conversation_id, title, user_id)
    if not success:
        # If conversation already exists, just return the ID
        pass
    
    return conversation_id

def add_user_message(conversation_id: str, question: str, metadata: Dict[str, Any] = None) -> bool:
    """Add user message to conversation"""
    return db.add_message(conversation_id, "user", question, metadata)

def add_assistant_message(conversation_id: str, answer: str, metadata: Dict[str, Any] = None) -> bool:
    """Add assistant message to conversation"""
    return db.add_message(conversation_id, "assistant", answer, metadata)

def get_conversation_context(conversation_id: str, max_messages: int = 10) -> List[Dict[str, str]]:
    """Get conversation context formatted for LLM"""
    messages = db.get_conversation_history(conversation_id, max_messages)
    
    # Convert to format expected by LLM
    context = []
    for msg in messages:
        context.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    return context

def conversation_exists(conversation_id: str) -> bool:
    """Check if conversation exists"""
    return db.get_conversation_info(conversation_id) is not None

def get_conversation_summary(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get conversation summary with basic info"""
    info = db.get_conversation_info(conversation_id)
    if not info:
        return None
    
    messages = db.get_conversation_history(conversation_id, 1)
    message_count = len(db.get_conversation_history(conversation_id, 1000))
    
    return {
        "conversation_id": info["conversation_id"],
        "title": info["title"],
        "created_at": info["created_at"],
        "last_updated": info["last_updated"],
        "message_count": message_count,
        "user_id": info["user_id"]
    }

def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation"""
    return db.delete_conversation(conversation_id)

def list_user_conversations(user_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """List conversations for a user"""
    return db.list_conversations(user_id, limit)

def update_conversation_title(conversation_id: str, title: str) -> bool:
    """Update conversation title"""
    return db.update_conversation_title(conversation_id, title)
