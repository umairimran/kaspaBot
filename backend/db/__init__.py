"""
Database package initialization
"""
from .database import db, ConversationDB
from .conversation_manager import (
    start_conversation, add_user_message, add_assistant_message,
    get_conversation_context, conversation_exists, get_conversation_summary,
    list_user_conversations, delete_conversation, update_conversation_title
)

__all__ = [
    'db', 'ConversationDB',
    'start_conversation', 'add_user_message', 'add_assistant_message',
    'get_conversation_context', 'conversation_exists', 'get_conversation_summary',
    'list_user_conversations', 'delete_conversation', 'update_conversation_title'
]
