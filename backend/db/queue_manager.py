#!/usr/bin/env python3
"""
Database Queue Manager for Twitter Bot

This module manages the Twitter bot response queue using SQLite database
instead of JSON files for better performance and reliability.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class DatabaseQueueManager:
    """Manages Twitter bot response queue using SQLite database"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use the same database as conversations
            db_path = Path(__file__).parent / "conversations.db"
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the queue table in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS twitter_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mention_id TEXT UNIQUE NOT NULL,
                    response_text TEXT NOT NULL,
                    conversation_id TEXT,
                    mention_data TEXT,  -- JSON string
                    priority INTEGER DEFAULT 0,
                    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted BOOLEAN DEFAULT FALSE,
                    posted_at TIMESTAMP NULL,
                    success BOOLEAN NULL,
                    reply_data TEXT,  -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create rate limit tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS twitter_rate_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    last_search_time TIMESTAMP DEFAULT 0,
                    last_post_reset TIMESTAMP DEFAULT 0,
                    posts_today INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create processed mentions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mention_id TEXT UNIQUE NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def add_response(self, mention_id: str, response_text: str, conversation_id: str, 
                    mention_data: Dict, priority: int = 0) -> bool:
        """Add a response to the queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if already exists
                cursor.execute("SELECT id FROM twitter_queue WHERE mention_id = ?", (mention_id,))
                if cursor.fetchone():
                    return False  # Already exists
                
                # Insert new response
                cursor.execute("""
                    INSERT INTO twitter_queue 
                    (mention_id, response_text, conversation_id, mention_data, priority, queued_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    mention_id,
                    response_text,
                    conversation_id,
                    json.dumps(mention_data),
                    priority,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error adding response to queue: {e}")
            return False
    
    def get_next_responses(self, count: int) -> List[Dict]:
        """Get next responses to post (sorted by priority and queued time)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT mention_id, response_text, conversation_id, mention_data, 
                           priority, queued_at, posted_at, success, reply_data
                    FROM twitter_queue 
                    WHERE posted = FALSE 
                    ORDER BY priority DESC, queued_at ASC 
                    LIMIT ?
                """, (count,))
                
                rows = cursor.fetchall()
                responses = []
                
                for row in rows:
                    responses.append({
                        "mention_id": row[0],
                        "response_text": row[1],
                        "conversation_id": row[2],
                        "mention_data": json.loads(row[3]) if row[3] else {},
                        "priority": row[4],
                        "queued_at": row[5],
                        "posted_at": row[6],
                        "success": row[7],
                        "reply_data": json.loads(row[8]) if row[8] else {}
                    })
                
                return responses
                
        except Exception as e:
            print(f"Error getting next responses: {e}")
            return []
    
    def get_all_responses(self, limit: int = 10) -> List[Dict]:
        """Get all responses (both posted and unposted) for interactions display"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT mention_id, response_text, conversation_id, mention_data, 
                           priority, queued_at, posted_at, success, reply_data, posted, created_at
                    FROM twitter_queue 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                responses = []
                
                for row in rows:
                    responses.append({
                        "mention_id": row[0],
                        "response_text": row[1],
                        "conversation_id": row[2],
                        "mention_data": row[3],  # Keep as string for now
                        "priority": row[4],
                        "queued_at": row[5],
                        "posted_at": row[6],
                        "success": row[7],
                        "reply_data": row[8],
                        "posted": row[9],
                        "created_at": row[10]
                    })
                
                return responses
                
        except Exception as e:
            print(f"Error getting all responses: {e}")
            return []
    
    def mark_posted(self, mention_id: str, success: bool, reply_data: Dict = None) -> bool:
        """Mark a response as posted"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE twitter_queue 
                    SET posted = TRUE, posted_at = ?, success = ?, reply_data = ?, updated_at = ?
                    WHERE mention_id = ?
                """, (
                    datetime.now().isoformat(),
                    success,
                    json.dumps(reply_data) if reply_data else None,
                    datetime.now().isoformat(),
                    mention_id
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error marking response as posted: {e}")
            return False
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM twitter_queue")
                total = cursor.fetchone()[0]
                
                # Get posted count
                cursor.execute("SELECT COUNT(*) FROM twitter_queue WHERE posted = TRUE")
                posted = cursor.fetchone()[0]
                
                # Get pending count
                cursor.execute("SELECT COUNT(*) FROM twitter_queue WHERE posted = FALSE")
                pending = cursor.fetchone()[0]
                
                return {
                    "total": total,
                    "posted": posted,
                    "pending": pending
                }
                
        except Exception as e:
            print(f"Error getting queue stats: {e}")
            return {"total": 0, "posted": 0, "pending": 0}
    
    def clear_pending_responses(self) -> int:
        """Clear all pending responses from queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM twitter_queue WHERE posted = FALSE")
                conn.commit()
                
                return cursor.rowcount
                
        except Exception as e:
            print(f"Error clearing pending responses: {e}")
            return 0
    
    def clear_all_responses(self) -> int:
        """Clear all responses from queue (both posted and unposted)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM twitter_queue")
                deleted_count = cursor.rowcount
                
                conn.commit()
                return deleted_count
                
        except Exception as e:
            print(f"Error clearing all responses: {e}")
            return 0
    
    def add_processed_mention(self, mention_id: str) -> bool:
        """Add a mention ID to processed list"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO processed_mentions (mention_id, processed_at)
                    VALUES (?, ?)
                """, (mention_id, datetime.now().isoformat()))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error adding processed mention: {e}")
            return False
    
    def is_mention_processed(self, mention_id: str) -> bool:
        """Check if a mention has been processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM processed_mentions WHERE mention_id = ?", (mention_id,))
                return cursor.fetchone() is not None
                
        except Exception as e:
            print(f"Error checking processed mention: {e}")
            return False
    
    def get_rate_limit_data(self) -> Dict:
        """Get rate limit tracking data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT last_search_time, last_post_reset, posts_today 
                    FROM twitter_rate_limits 
                    ORDER BY id DESC LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    return {
                        "last_search_time": row[0],
                        "last_post_reset": row[1],
                        "posts_today": row[2]
                    }
                else:
                    # Initialize with default values
                    return {
                        "last_search_time": 0,
                        "last_post_reset": 0,
                        "posts_today": 0
                    }
                
        except Exception as e:
            print(f"Error getting rate limit data: {e}")
            return {"last_search_time": 0, "last_post_reset": 0, "posts_today": 0}
    
    def update_rate_limit_data(self, data: Dict) -> bool:
        """Update rate limit tracking data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or update rate limit data
                cursor.execute("""
                    INSERT OR REPLACE INTO twitter_rate_limits 
                    (id, last_search_time, last_post_reset, posts_today, updated_at)
                    VALUES (1, ?, ?, ?, ?)
                """, (
                    data.get("last_search_time", 0),
                    data.get("last_post_reset", 0),
                    data.get("posts_today", 0),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating rate limit data: {e}")
            return False
