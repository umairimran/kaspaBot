#!/usr/bin/env python3
"""
Twitter Bot Integration for Kaspa RAG Backend

This module integrates the Twitter bot with the main FastAPI application,
providing REST APIs for queue management and bot control.
"""

import os
import sys
import threading
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Add twitter_automation directory to path
twitter_automation_dir = Path(__file__).parent / "twitter_automation"
sys.path.insert(0, str(twitter_automation_dir))

from optimized_mention_bot import TwitterBot, ResponseQueue, RateLimitTracker
from db.queue_manager import DatabaseQueueManager

class TwitterBotManager:
    """Manages the Twitter bot instance and provides API endpoints"""
    
    def __init__(self):
        self.bot = None
        self.bot_thread = None
        self.is_running = False
        self.start_time = None
        self.error_count = 0
        self.last_error = None
        
    def start_bot(self) -> Dict:
        """Start the Twitter bot in a background thread"""
        try:
            if self.is_running:
                return {
                    "success": False,
                    "message": "Bot is already running",
                    "status": "running"
                }
            
            # Check if credentials are available
            required_vars = [
                "TWITTER_BEARER_TOKEN",
                "TWITTER_API_KEY", 
                "TWITTER_API_SECRET",
                "TWITTER_ACCESS_TOKEN",
                "TWITTER_ACCESS_TOKEN_SECRET"
            ]
            
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                return {
                    "success": False,
                    "message": f"Missing Twitter API credentials. Please set: {', '.join(missing_vars)}",
                    "status": "error",
                    "missing_credentials": True
                }
            
            # Initialize bot
            self.bot = TwitterBot()
            
            # Start bot in background thread
            self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
            self.bot_thread.start()
            
            self.is_running = True
            self.start_time = datetime.now()
            self.error_count = 0
            self.last_error = None
            
            return {
                "success": True,
                "message": "Twitter bot started successfully",
                "status": "running",
                "start_time": self.start_time.isoformat()
            }
            
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            return {
                "success": False,
                "message": f"Failed to start bot: {str(e)}",
                "status": "error"
            }
    
    def stop_bot(self) -> Dict:
        """Stop the Twitter bot"""
        try:
            if not self.is_running:
                return {
                    "success": False,
                    "message": "Bot is not running",
                    "status": "stopped"
                }
            
            self.is_running = False
            
            # Wait for thread to finish (with timeout)
            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=5)
            
            return {
                "success": True,
                "message": "Twitter bot stopped successfully",
                "status": "stopped"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to stop bot: {str(e)}",
                "status": "error"
            }
    
    def get_bot_status(self) -> Dict:
        """Get current bot status"""
        try:
            status = {
                "is_running": self.is_running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "error_count": self.error_count,
                "last_error": self.last_error,
                "uptime_seconds": None
            }
            
            if self.start_time:
                status["uptime_seconds"] = (datetime.now() - self.start_time).total_seconds()
            
            # Get queue and rate limit info
            if self.bot:
                queue_stats = self.bot.response_queue.get_queue_stats()
                posts_remaining = self.bot.rate_tracker.get_posts_remaining()
                
                # Calculate search timing
                last_search_time = self.bot.rate_tracker.data.get("last_search_time", 0)
                next_search_time = last_search_time + 900  # 15 minutes
                
                status.update({
                    "queue_stats": queue_stats,
                    "posts_remaining_today": posts_remaining,
                    "rate_limits": {
                        "search_interval_minutes": 15,
                        "daily_post_limit": 17
                    },
                    "last_search_time": datetime.fromtimestamp(last_search_time).isoformat() if last_search_time > 0 else None,
                    "next_search_time": datetime.fromtimestamp(next_search_time).isoformat() if last_search_time > 0 else None
                })
            
            return {
                "success": True,
                "status": status
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting bot status: {str(e)}"
            }
    
    def get_queue_status(self) -> Dict:
        """Get response queue status"""
        try:
            if not self.bot:
                return {
                    "success": False,
                    "message": "Bot not initialized"
                }
            
            queue_stats = self.bot.response_queue.get_queue_stats()
            posts_remaining = self.bot.rate_tracker.get_posts_remaining()
            
            # Get pending responses from database
            db_queue = DatabaseQueueManager()
            pending_responses = db_queue.get_next_responses(10)  # Get first 10
            
            # Format responses for API
            formatted_responses = []
            for item in pending_responses:
                formatted_responses.append({
                    "mention_id": item["mention_id"],
                    "response_text": item["response_text"][:100] + "..." if len(item["response_text"]) > 100 else item["response_text"],
                    "priority": item["priority"],
                    "queued_at": item["queued_at"]
                })
            
            return {
                "success": True,
                "queue_stats": queue_stats,
                "posts_remaining_today": posts_remaining,
                "pending_responses": formatted_responses
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting queue status: {str(e)}"
            }
    
    def clear_queue(self) -> Dict:
        """Clear all pending responses from queue"""
        try:
            if not self.bot:
                return {
                    "success": False,
                    "message": "Bot not initialized"
                }
            
            # Clear pending responses from database
            db_queue = DatabaseQueueManager()
            cleared_count = db_queue.clear_pending_responses()
            
            return {
                "success": True,
                "message": f"Queue cleared successfully. Removed {cleared_count} pending responses."
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error clearing queue: {str(e)}"
            }
    
    def get_recent_interactions(self, limit: int = 10) -> Dict:
        """Get recent Twitter interactions from database"""
        try:
            # Get interactions from database queue
            db_queue = DatabaseQueueManager()
            
            # Get all responses (both posted and unposted) ordered by creation time
            all_responses = db_queue.get_all_responses(limit)
            
            # Format interactions
            formatted_interactions = []
            for response in all_responses:
                mention_data = response.get("mention_data", {})
                if isinstance(mention_data, str):
                    try:
                        mention_data = json.loads(mention_data)
                    except:
                        mention_data = {}
                
                formatted_interaction = {
                    "timestamp": response.get("queued_at", response.get("created_at", "")),
                    "mention_id": response["mention_id"],
                    "conversation_id": response.get("conversation_id"),
                    "reply_posted": response.get("posted", False),
                    "ai_response": response["response_text"][:100] + "..." if len(response["response_text"]) > 100 else response["response_text"],
                    "mention_text": mention_data.get("mention_text", "N/A")
                }
                
                formatted_interactions.append(formatted_interaction)
            
            return {
                "success": True,
                "interactions": formatted_interactions,
                "total_count": len(formatted_interactions)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting interactions: {str(e)}"
            }
    
    def clear_interactions(self) -> Dict:
        """Clear all interaction history from database"""
        try:
            # Clear all responses from database queue
            db_queue = DatabaseQueueManager()
            cleared_count = db_queue.clear_all_responses()
            
            return {
                "success": True,
                "message": f"Interaction history cleared successfully. Removed {cleared_count} interactions."
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error clearing interactions: {str(e)}"
            }
    
    def _run_bot(self):
        """Run the bot in background thread"""
        try:
            # The TwitterBot.run() method handles the continuous loop and immediate first API call
            self.bot.run()
        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            print(f"💥 Fatal bot error: {e}")
        finally:
            self.is_running = False

# Global bot manager instance
bot_manager = TwitterBotManager()
