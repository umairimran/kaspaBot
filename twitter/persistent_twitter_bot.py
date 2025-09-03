"""
Persistent Context-Aware Twitter Bot for Kaspa
Solves the "next day context" problem using SQLite database storage
"""

import tweepy
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import hashlib

# Import our persistent conversation manager
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from persistent_conversation_manager import PersistentConversationManager

class PersistentKaspaBot:
    """
    Twitter bot with persistent conversation memory.
    Can remember conversations across days, weeks, or even months.
    """
    
    def __init__(self, api_url="http://localhost:8000", db_path="kaspa_twitter_conversations.db"):
        self.api_url = api_url
        self.persistent_conv_manager = PersistentConversationManager(
            db_path=db_path,
            context_days=90  # Keep context for 3 months
        )
        
        # Twitter API credentials (set these as environment variables)
        self.bearer_token = "YOUR_BEARER_TOKEN"  # Set from environment
        self.api_key = "YOUR_API_KEY"
        self.api_secret = "YOUR_API_SECRET"
        self.access_token = "YOUR_ACCESS_TOKEN"
        self.access_token_secret = "YOUR_ACCESS_TOKEN_SECRET"
        
        # Initialize Twitter API v2 client
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True
        )
        
        print(f"🤖 Persistent KaspaBot initialized with database: {db_path}")
        print(f"📊 Context retention: {self.persistent_conv_manager.context_days} days")
    
    def extract_conversation_id_from_tweet(self, tweet) -> str:
        """
        Extract conversation ID from tweet.
        Uses thread ID for replies, or creates new ID for mentions.
        """
        if hasattr(tweet, 'conversation_id') and tweet.conversation_id:
            return f"twitter_conv_{tweet.conversation_id}"
        elif hasattr(tweet, 'in_reply_to_tweet_id') and tweet.in_reply_to_tweet_id:
            return f"twitter_conv_{tweet.in_reply_to_tweet_id}"
        else:
            # New conversation - use tweet ID
            return f"twitter_conv_{tweet.id}"
    
    def get_user_id_from_tweet(self, tweet) -> str:
        """Extract user ID from tweet."""
        if hasattr(tweet, 'author_id'):
            return str(tweet.author_id)
        return "unknown_user"
    
    def clean_tweet_text(self, text: str) -> str:
        """Clean tweet text by removing mentions and URLs."""
        # Remove @mentions except the bot mention
        text = re.sub(r'@\w+', '', text).strip()
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        # Clean up extra spaces
        text = ' '.join(text.split())
        return text.strip()
    
    def get_conversation_context_summary(self, conversation_id: str, days_back: int = 30) -> str:
        """
        Get a human-readable summary of conversation context.
        Shows how much history exists and from when.
        """
        context_messages = self.persistent_conv_manager.get_context_messages(
            conversation_id, 
            max_messages=20, 
            days_back=days_back
        )
        
        if not context_messages:
            return "🆕 New conversation"
        
        first_msg = context_messages[0]
        try:
            first_time = datetime.fromisoformat(first_msg["timestamp"].replace("Z", "+00:00"))
            time_diff = datetime.now() - first_time.replace(tzinfo=None)
            
            if time_diff.days == 0:
                time_str = "today"
            elif time_diff.days == 1:
                time_str = "yesterday"
            elif time_diff.days <= 7:
                time_str = f"{time_diff.days} days ago"
            elif time_diff.days <= 30:
                weeks = time_diff.days // 7
                time_str = f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = time_diff.days // 30
                time_str = f"{months} month{'s' if months > 1 else ''} ago"
                
            return f"📚 Conversation started {time_str} ({len(context_messages)} messages)"
        except:
            return f"📚 Continuing conversation ({len(context_messages)} messages)"
    
    async def query_kaspa_api(self, question: str, conversation_id: str, user_id: str, tweet_id: str = None, context_days: int = 30) -> Tuple[str, bool, Optional[int]]:
        """
        Query the Kaspa API with persistent conversation context.
        Returns: (answer, has_context, context_days_back)
        """
        try:
            payload = {
                "query": question,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "tweet_id": tweet_id,
                "context_days": context_days
            }
            
            response = requests.post(f"{self.api_url}/ask", json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get("answer", ""), data.get("has_context", False), data.get("context_days_back")
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            return "Sorry, I'm having trouble processing your question right now. Please try again later.", False, None
    
    def format_response_for_twitter(self, answer: str, has_context: bool, context_days_back: Optional[int], conversation_summary: str) -> str:
        """
        Format the response for Twitter with context indicators.
        """
        # Remove existing emoji prefixes from API response
        clean_answer = re.sub(r'^[🤖💬📅📆🗓️]\s*', '', answer)
        
        # Add context-aware emoji based on conversation age
        if not has_context:
            prefix = "🤖"  # New conversation
        elif context_days_back is not None:
            if context_days_back == 0:
                prefix = "💬"  # Same day
            elif context_days_back <= 1:
                prefix = "📅"  # Yesterday  
            elif context_days_back <= 7:
                prefix = "📆"  # This week
            else:
                prefix = "🗓️"  # Older conversation
        else:
            prefix = "💬"  # Default for existing context
        
        formatted_response = f"{prefix} {clean_answer}"
        
        # Ensure it fits Twitter's character limit
        if len(formatted_response) > 280:
            # Try to truncate gracefully
            max_content = 280 - len(prefix) - 4  # Account for prefix and "..."
            truncated = clean_answer[:max_content].rsplit(' ', 1)[0]
            formatted_response = f"{prefix} {truncated}..."
        
        return formatted_response
    
    def should_respond_to_tweet(self, tweet) -> bool:
        """
        Determine if the bot should respond to a tweet.
        """
        # Skip if bot authored the tweet
        if hasattr(tweet, 'author_id') and str(tweet.author_id) == str(self.client.get_me().data.id):
            return False
        
        # Skip retweets
        if hasattr(tweet, 'text') and tweet.text.startswith('RT @'):
            return False
        
        # Must mention the bot or be a reply to the bot
        bot_username = self.client.get_me().data.username.lower()
        tweet_text = tweet.text.lower()
        
        is_mention = f"@{bot_username}" in tweet_text
        is_reply_to_bot = hasattr(tweet, 'in_reply_to_user_id') and tweet.in_reply_to_user_id == self.client.get_me().data.id
        
        return is_mention or is_reply_to_bot
    
    async def respond_to_tweet(self, tweet):
        """
        Generate and post a response to a tweet with persistent context awareness.
        """
        try:
            # Extract conversation details
            conversation_id = self.extract_conversation_id_from_tweet(tweet)
            user_id = self.get_user_id_from_tweet(tweet)
            tweet_id = str(tweet.id)
            
            # Get conversation context summary for logging
            context_summary = self.get_conversation_context_summary(conversation_id)
            print(f"📝 Processing tweet {tweet_id}: {context_summary}")
            
            # Clean the tweet text
            question = self.clean_tweet_text(tweet.text)
            
            if not question:
                print("⚠️ Empty question after cleaning, skipping")
                return
            
            # Get response from API with persistent context
            answer, has_context, context_days_back = await self.query_kaspa_api(
                question, 
                conversation_id, 
                user_id, 
                tweet_id,
                context_days=30  # Look back 30 days for context
            )
            
            # Format response for Twitter
            formatted_response = self.format_response_for_twitter(
                answer, 
                has_context, 
                context_days_back, 
                context_summary
            )
            
            # Post reply
            reply = self.client.create_tweet(
                text=formatted_response,
                in_reply_to_tweet_id=tweet.id
            )
            
            if reply.data:
                context_type = "with context" if has_context else "new conversation"
                days_info = f" ({context_days_back} days back)" if context_days_back is not None else ""
                print(f"✅ Replied to @{tweet.author_id}: {context_type}{days_info}")
                print(f"📤 Response: {formatted_response[:100]}...")
            else:
                print("❌ Failed to post reply")
                
        except Exception as e:
            print(f"❌ Error responding to tweet {tweet.id}: {e}")
    
    def run_bot(self, check_interval: int = 60):
        """
        Main bot loop with persistent conversation support.
        """
        print(f"🚀 Starting Persistent KaspaBot...")
        print(f"🔄 Check interval: {check_interval} seconds")
        
        # Get initial stats
        stats = self.persistent_conv_manager.get_stats()
        print(f"📊 Database stats: {stats['total_conversations']} conversations, {stats['database_size_mb']} MB")
        
        last_check = datetime.now()
        
        while True:
            try:
                print(f"\n🔍 Checking for mentions since {last_check.strftime('%H:%M:%S')}...")
                
                # Get bot's user ID
                bot_user = self.client.get_me()
                
                # Search for recent mentions
                query = f"@{bot_user.data.username} -is:retweet"
                tweets = self.client.search_recent_tweets(
                    query=query,
                    tweet_fields=['author_id', 'conversation_id', 'in_reply_to_user_id', 'created_at'],
                    max_results=10
                )
                
                if tweets.data:
                    print(f"📬 Found {len(tweets.data)} mention(s)")
                    
                    for tweet in tweets.data:
                        # Check if we should respond
                        if self.should_respond_to_tweet(tweet):
                            # Check if we've already responded (avoid duplicates)
                            conversation_id = self.extract_conversation_id_from_tweet(tweet)
                            
                            # Simple duplicate check - you might want to enhance this
                            await self.respond_to_tweet(tweet)
                            
                            # Small delay between responses
                            time.sleep(2)
                else:
                    print("📭 No new mentions found")
                
                # Periodic cleanup (once per hour)
                if datetime.now() - last_check > timedelta(hours=1):
                    print("🧹 Running periodic cleanup...")
                    cleaned = self.persistent_conv_manager.cleanup_old_conversations(days_to_keep=90)
                    if cleaned > 0:
                        print(f"🗑️ Cleaned up {cleaned} old conversations")
                
                last_check = datetime.now()
                
                # Wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Bot error: {e}")
                print("⏸️ Waiting 5 minutes before retry...")
                time.sleep(300)  # Wait 5 minutes on error
    
    def get_conversation_history(self, conversation_id: str, days_back: int = 30) -> List[Dict]:
        """Get conversation history for debugging/analysis."""
        return self.persistent_conv_manager.get_context_messages(conversation_id, max_messages=50, days_back=days_back)
    
    def get_user_conversation_summary(self, user_id: str, days_back: int = 30) -> Dict:
        """Get summary of all conversations with a specific user."""
        conversations = self.persistent_conv_manager.get_user_conversations(user_id, days_back)
        
        total_messages = 0
        for conv in conversations:
            total_messages += conv.get('message_count', 0)
        
        return {
            "user_id": user_id,
            "total_conversations": len(conversations),
            "total_messages": total_messages,
            "conversations": conversations
        }


async def main():
    """Test the persistent bot functionality."""
    bot = PersistentKaspaBot()
    
    # Example: Test persistent context
    conv_id = "test_persistent_conv"
    user_id = "test_user_123"
    
    print("Testing persistent conversation context...")
    
    # Day 1: First question
    answer1, has_context1, days_back1 = await bot.query_kaspa_api(
        "What is GHOSTDAG?", 
        conv_id, 
        user_id
    )
    print(f"Day 1 - Answer: {answer1}")
    print(f"Day 1 - Has context: {has_context1}")
    
    # Simulate Day 2: Follow-up question (context should persist!)
    answer2, has_context2, days_back2 = await bot.query_kaspa_api(
        "How does it compare to Bitcoin's consensus?", 
        conv_id, 
        user_id
    )
    print(f"Day 2 - Answer: {answer2}")
    print(f"Day 2 - Has context: {has_context2}")
    print(f"Day 2 - Days back: {days_back2}")
    
    # Show conversation history
    history = bot.get_conversation_history(conv_id)
    print(f"Conversation history: {len(history)} messages")
    
    # Show stats
    stats = bot.persistent_conv_manager.get_stats()
    print(f"Database stats: {stats}")


if __name__ == "__main__":
    import asyncio
    
    # Run test
    asyncio.run(main())
    
    # Uncomment to run the actual bot
    # bot = PersistentKaspaBot()
    # bot.run_bot(check_interval=60)
