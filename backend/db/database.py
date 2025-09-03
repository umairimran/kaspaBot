"""
SQL Database utility for conversation history management
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

DB_PATH = Path(__file__).parent / "conversations.db"

class ConversationDB:
    def __init__(self):
        self.db_path = str(DB_PATH)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    title TEXT,
                    user_id TEXT
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
            """)
            
            # Indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_id ON messages(conversation_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)")
            
            conn.commit()
    
    def create_conversation(self, conversation_id: str, title: str = None, user_id: str = None) -> bool:
        """Create a new conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (conversation_id, title, user_id)
                    VALUES (?, ?, ?)
                """, (conversation_id, title, user_id))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def add_message(self, conversation_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a message to a conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure conversation exists
                cursor.execute("SELECT 1 FROM conversations WHERE conversation_id = ?", (conversation_id,))
                if not cursor.fetchone():
                    self.create_conversation(conversation_id)
                
                # Add message
                metadata_json = json.dumps(metadata) if metadata else None
                cursor.execute("""
                    INSERT INTO messages (conversation_id, role, content, metadata)
                    VALUES (?, ?, ?, ?)
                """, (conversation_id, role, content, metadata_json))
                
                # Update conversation last_updated
                cursor.execute("""
                    UPDATE conversations 
                    SET last_updated = CURRENT_TIMESTAMP 
                    WHERE conversation_id = ?
                """, (conversation_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding message: {e}")
            return False
    
    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a given conversation ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, metadata, timestamp
                FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (conversation_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                role, content, metadata_json, timestamp = row
                metadata = json.loads(metadata_json) if metadata_json else {}
                messages.append({
                    "role": role,
                    "content": content,
                    "metadata": metadata,
                    "timestamp": timestamp
                })
            
            return messages
    
    def get_conversation_info(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT conversation_id, created_at, last_updated, title, user_id
                FROM conversations
                WHERE conversation_id = ?
            """, (conversation_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "conversation_id": row[0],
                    "created_at": row[1],
                    "last_updated": row[2],
                    "title": row[3],
                    "user_id": row[4]
                }
            return None
    
    def list_conversations(self, user_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List conversations, optionally filtered by user_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    SELECT conversation_id, created_at, last_updated, title, user_id
                    FROM conversations
                    WHERE user_id = ?
                    ORDER BY last_updated DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT conversation_id, created_at, last_updated, title, user_id
                    FROM conversations
                    ORDER BY last_updated DESC
                    LIMIT ?
                """, (limit,))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    "conversation_id": row[0],
                    "created_at": row[1],
                    "last_updated": row[2],
                    "title": row[3],
                    "user_id": row[4]
                })
            
            return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE conversations 
                    SET title = ?, last_updated = CURRENT_TIMESTAMP 
                    WHERE conversation_id = ?
                """, (title, conversation_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating conversation title: {e}")
            return False

# Global instance
db = ConversationDB()
