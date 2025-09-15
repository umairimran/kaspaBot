#!/usr/bin/env python3
"""
Optimized Twitter Mention Bot with API Rate Limiting and Queue Management

This bot:
1. Monitors mentions every 15 minutes (respecting 1 request/15min limit)
2. Generates AI responses for new mentions
3. Queues responses and posts only 17 per day (respecting 17 requests/24h limit)
4. Prevents duplicate replies
5. Runs continuously with proper error handling
"""

import os
import requests
import time
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session
from typing import Dict, List, Set, Optional
from pathlib import Path

# Load environment variables from current directory (Docker working dir)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_bot.log'),
        logging.StreamHandler()
    ]
)

# Configuration
BEARER = os.getenv("TWITTER_BEARER_TOKEN")
CONSUMER_KEY = os.getenv("TWITTER_API_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

BOT_HANDLE = os.getenv("BOT_HANDLE")
BACKEND_URL = os.getenv("BACKEND_URL")

# API Rate Limits (Basic Plan)
SEARCH_RATE_LIMIT = 15  # 15 seconds between search requests (60 requests per 15 mins) 
POST_RATE_LIMIT = 100     # 100 posts per 24 hours
POST_WINDOW = 86400       # 24 hours in seconds

# Import database queue manager
import sys
sys.path.append(str(Path(__file__).parent.parent))
from db.queue_manager import DatabaseQueueManager

# Initialize database queue manager
db_queue = DatabaseQueueManager()

class RateLimitTracker:
    """Tracks API rate limits and usage using database"""
    
    def __init__(self):
        self.data = self.load_tracker()
    
    def load_tracker(self) -> Dict:
        """Load rate limit tracking data from database"""
        return db_queue.get_rate_limit_data()
    
    def save_tracker(self):
        """Save rate limit tracking data to database"""
        db_queue.update_rate_limit_data(self.data)
    
    def can_search(self) -> bool:
        """Check if we can make a search request"""
        current_time = time.time()
        last_search = self.data.get("last_search_time", 0)
        return (current_time - last_search) >= SEARCH_RATE_LIMIT
    
    def can_post(self) -> bool:
        """Check if we can post a tweet"""
        current_time = time.time()
        last_reset = self.data.get("last_post_reset", 0)
        posts_today = self.data.get("posts_today", 0)
        
        # Reset daily counter if 24 hours have passed
        if (current_time - last_reset) >= POST_WINDOW:
            self.data["posts_today"] = 0
            self.data["last_post_reset"] = current_time
            posts_today = 0
        
        return posts_today < POST_RATE_LIMIT
    
    def record_search(self):
        """Record that we made a search request"""
        self.data["last_search_time"] = time.time()
        self.save_tracker()
    
    def record_post(self):
        """Record that we posted a tweet"""
        self.data["posts_today"] = self.data.get("posts_today", 0) + 1
        self.save_tracker()
    
    def get_posts_remaining(self) -> int:
        """Get number of posts remaining today"""
        current_time = time.time()
        last_reset = self.data.get("last_post_reset", 0)
        posts_today = self.data.get("posts_today", 0)
        
        # Reset daily counter if 24 hours have passed
        if (current_time - last_reset) >= POST_WINDOW:
            return POST_RATE_LIMIT
        
        return max(0, POST_RATE_LIMIT - posts_today)

class ResponseQueue:
    """Manages the queue of responses to be posted using database"""
    
    def __init__(self):
        pass  # No need to load queue into memory, we'll query database directly
    
    def load_queue(self) -> List[Dict]:
        """Load response queue from database"""
        return db_queue.get_next_responses(1000)  # Get all pending responses
    
    def save_queue(self):
        """Save response queue to database - not needed as we save directly"""
        pass
    
    def add_response(self, mention_id: str, response_text: str, conversation_id: str, 
                    mention_data: Dict, priority: int = 0):
        """Add a response to the queue"""
        success = db_queue.add_response(mention_id, response_text, conversation_id, mention_data, priority)
        
        if success:
            logging.info(f"📝 Added response to queue for mention {mention_id}")
        else:
            logging.info(f"⚠️ Response already in queue for mention {mention_id}")
    
    def get_next_responses(self, count: int) -> List[Dict]:
        """Get next responses to post (sorted by priority and queued time)"""
        return db_queue.get_next_responses(count)
    
    def mark_posted(self, mention_id: str, success: bool, reply_data: Dict = None):
        """Mark a response as posted"""
        db_queue.mark_posted(mention_id, success, reply_data)
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        return db_queue.get_queue_stats()

class MentionProcessor:
    """Handles mention processing and AI response generation"""
    
    def __init__(self):
        pass  # No need to load processed mentions into memory
    
    def load_processed_mentions(self) -> Set[str]:
        """Load previously processed mention IDs from database"""
        # This method is kept for compatibility but not used
        return set()
    
    def save_processed_mentions(self):
        """Save processed mention IDs to database"""
        # This method is kept for compatibility but not used
        pass
    
    def get_ai_response(self, question: str, conversation_id: str) -> str:
        """Get AI response from backend"""
        try:
            response = requests.post(f"{BACKEND_URL}/ask", json={
                "question": question,
                "conversation_id": conversation_id,
                "user_id": "twitter_user"
            }, timeout=30)
            
            print(f"🔍 DEBUG: Backend API response status: {response.status_code}")
            print(f"🔍 DEBUG: Backend API response text: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "Sorry, I couldn't process your question.")
                return answer
            else:
                print(f"🔍 DEBUG: Non-200 status code: {response.status_code}")
                return "Sorry, I'm experiencing technical difficulties."
        except Exception as e:
            logging.error(f"❌ Error getting AI response: {e}")
            return "Sorry, I'm currently unavailable."
    
    def extract_question_from_mention(self, mention_text: str, bot_handle: str) -> str:
        """Extract the actual question from mention text"""
        question = mention_text.replace(bot_handle, "").strip()
        
        prefixes_to_remove = [
            "hey", "hi", "hello", "can you", "could you", "please", 
            "thoughts?", "thoughts on", "what do you think", "opinion on",
            "explain", "tell me about", "what is", "how does"
        ]
        
        words = question.split()
        while words and words[0].lower().rstrip('?.,!') in prefixes_to_remove:
            words.pop(0)
        
        cleaned_question = " ".join(words).strip()
        return cleaned_question if len(cleaned_question) >= 3 else ""
    
    def get_original_tweet_content(self, conversation_id: str, headers: Dict) -> Optional[str]:
        """Get the content of the original tweet in the conversation"""
        try:
            if conversation_id:
                tweet_url = f"https://api.twitter.com/2/tweets/{conversation_id}"
                response = requests.get(tweet_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("text", "")
        except Exception as e:
            logging.error(f"❌ Error fetching original tweet: {e}")
        return None
    
    def process_mentions(self, mentions: List[Dict], headers: Dict) -> List[Dict]:
        """Process mentions and generate responses"""
        processed_responses = []
        
        for mention in mentions:
            mention_id = mention["id"]
            
            # Skip if already processed (posted or in queue)
            if db_queue.is_mention_processed(mention_id):
                continue
            
            try:
                mention_text = mention["text"]
                conversation_id = mention["conversation_id"]
                author_id = mention["author_id"]
                created_at = mention.get("created_at", "")
                
                # Get original tweet content if this is a reply
                original_content = None
                if conversation_id and conversation_id != mention_id:
                    original_content = self.get_original_tweet_content(conversation_id, headers)
                
                # Extract the actual question
                question = self.extract_question_from_mention(mention_text, BOT_HANDLE)
                
                # Build context question
                if original_content and question:
                    context_question = f"Original post: '{original_content}'\n\nUser's question/mention: '{question}'"
                elif original_content and not question:
                    context_question = f"Please explain or comment on this: '{original_content}'"
                elif question:
                    context_question = question
                else:
                    context_question = "Hello! How can I help you with Kaspa?"
                
                # Get AI response
                ai_response = self.get_ai_response(context_question, conversation_id)
                
                # Check if AI response is unavailable
                if ai_response == "Sorry, I'm currently unavailable.":
                    print(f"⚠️ [AI] Skipping mention {mention_id} - AI unavailable")
                    logging.info(f"⚠️ Skipping mention {mention_id} - AI response unavailable")
                    # Still mark as processed to avoid re-processing
                    db_queue.add_processed_mention(mention_id)
                    continue
                
                # Enforce strict 280 character limit for Twitter
                if len(ai_response) > 280:
                    ai_response = ai_response[:277] + "..."
                
                # Create response data
                response_data = {
                    "mention_id": mention_id,
                    "response_text": ai_response,
                    "conversation_id": conversation_id,
                    "mention_data": {
                        "mention_text": mention_text,
                        "author_id": author_id,
                        "created_at": created_at,
                        "original_content": original_content,
                        "extracted_question": question,
                        "context_question": context_question
                    },
                    "priority": 1 if question else 0  # Higher priority for actual questions
                }
                
                processed_responses.append(response_data)
                db_queue.add_processed_mention(mention_id)
                
                logging.info(f"✅ Processed mention {mention_id}: {question[:50]}...")
                
            except Exception as e:
                logging.error(f"❌ Error processing mention {mention_id}: {e}")
                continue
        
        return processed_responses

class TwitterBot:
    """Main Twitter bot class"""
    
    def __init__(self):
        self.rate_tracker = RateLimitTracker()
        self.response_queue = ResponseQueue()
        self.mention_processor = MentionProcessor()
        
        # Validate credentials
        if not all([BEARER, CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
            raise ValueError("Missing required Twitter API credentials")
    
    def search_mentions(self) -> List[Dict]:
        """Search for new mentions"""
        if not self.rate_tracker.can_search():
            wait_time = SEARCH_RATE_LIMIT - (time.time() - self.rate_tracker.data.get("last_search_time", 0))
            logging.info(f"⏰ Rate limited. Waiting {wait_time:.0f} seconds...")
            return []
        
        try:
            mentions_url = "https://api.twitter.com/2/tweets/search/recent"
            params = {
                "query": BOT_HANDLE,
                "tweet.fields": "author_id,conversation_id,in_reply_to_user_id,created_at",
                "max_results": 10
            }
            headers = {"Authorization": f"Bearer {BEARER}"}
            
            print(f"🔍 [TWITTER API] Calling search API: {mentions_url}")
            print(f"📋 [TWITTER API] Query: {BOT_HANDLE}")
            logging.info("🔍 Searching for mentions...")
            response = requests.get(mentions_url, params=params, headers=headers, timeout=10)
            
            print(f"📊 [TWITTER API] Search response status: {response.status_code}")
            
            if response.status_code == 429:
                print("⏰ [TWITTER API] Rate limited!")
                logging.warning("⏰ Rate limited by Twitter API")
                return []
            elif response.status_code != 200:
                print(f"❌ [TWITTER API] Error: {response.status_code}")
                logging.error(f"❌ Error fetching mentions: {response.status_code}")
                return []
            
            data = response.json()
            mentions = data.get("data", [])
            
            print(f"✅ [TWITTER API] Found {len(mentions)} mentions")
            self.rate_tracker.record_search()
            logging.info(f"✅ Found {len(mentions)} mentions")
            return mentions
            
        except Exception as e:
            logging.error(f"❌ Error searching mentions: {e}")
            return []
    
    def post_tweet(self, reply_text: str, reply_to_id: str) -> Optional[Dict]:
        """Post a reply to a tweet"""
        try:
            url = "https://api.twitter.com/2/tweets"
            payload = {
                "text": reply_text,
                "reply": {"in_reply_to_tweet_id": reply_to_id}
            }
            auth = OAuth1Session(
                CONSUMER_KEY,
                client_secret=CONSUMER_SECRET,
                resource_owner_key=ACCESS_TOKEN,
                resource_owner_secret=ACCESS_TOKEN_SECRET,
            )
            
            print(f"📤 [TWITTER API] Calling post API: {url}")
            print(f"📝 [TWITTER API] Replying to tweet: {reply_to_id}")
            print(f"💬 [TWITTER API] Reply text: {reply_text[:100]}...")
            
            response = auth.post(url, json=payload)
            
            print(f"📊 [TWITTER API] Post response status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                self.rate_tracker.record_post()
                print(f"✅ [TWITTER API] Successfully posted reply!")
                logging.info(f"✅ Posted reply: {reply_text[:50]}...")
                return result
            else:
                print(f"❌ [TWITTER API] Failed to post: {response.status_code}")
                logging.error(f"❌ Failed to post reply: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"💥 [TWITTER API] Exception: {e}")
            logging.error(f"❌ Error posting reply: {e}")
            return None
    
    def process_queue(self):
        """Process responses from the queue (only unposted items)"""
        if not self.rate_tracker.can_post():
            posts_remaining = self.rate_tracker.get_posts_remaining()
            print(f"⏰ [QUEUE] Daily post limit reached. Posts remaining: {posts_remaining}")
            logging.info(f"⏰ Daily post limit reached. Posts remaining: {posts_remaining}")
            return
        
        posts_remaining = self.rate_tracker.get_posts_remaining()
        responses_to_post = self.response_queue.get_next_responses(posts_remaining)
        
        if not responses_to_post:
            print("📭 [QUEUE] No unposted responses in queue to post")
            logging.info("📭 No unposted responses in queue to post")
            return
        
        print(f"📤 [QUEUE] Processing {len(responses_to_post)} unposted responses from queue...")
        logging.info(f"📤 Posting {len(responses_to_post)} unposted responses from queue...")
        
        for i, response_data in enumerate(responses_to_post, 1):
            mention_id = response_data["mention_id"]
            response_text = response_data["response_text"]
            
            print(f"📝 [QUEUE] Posting {i}/{len(responses_to_post)}: {mention_id}")
            
            try:
                result = self.post_tweet(response_text, mention_id)
                
                if result:
                    reply_data = {
                        "success": True,
                        "reply_id": result.get("data", {}).get("id"),
                        "posted_at": datetime.now().isoformat()
                    }
                    # Mark as posted (posted=TRUE) - will never be processed again
                    self.response_queue.mark_posted(mention_id, True, reply_data)
                    print(f"✅ [QUEUE] Successfully posted reply for mention {mention_id} - marked as posted")
                    logging.info(f"✅ Successfully posted reply for mention {mention_id} - marked as posted")
                else:
                    # Mark as failed but still posted=FALSE so it can be retried later
                    self.response_queue.mark_posted(mention_id, False)
                    print(f"❌ [QUEUE] Failed to post reply for mention {mention_id} - will retry later")
                    logging.error(f"❌ Failed to post reply for mention {mention_id} - will retry later")
                
                # Small delay between posts
                if i < len(responses_to_post):  # Don't delay after the last post
                    print("⏳ [QUEUE] Waiting 2 seconds before next post...")
                    time.sleep(2)
                
            except Exception as e:
                print(f"💥 [QUEUE] Error posting response for {mention_id}: {e}")
                logging.error(f"❌ Error posting response for {mention_id}: {e}")
                # Mark as failed but keep posted=FALSE for retry
                self.response_queue.mark_posted(mention_id, False)
    
    
    def run_cycle(self):
        """Run one complete cycle of the bot"""
        try:
            current_time = datetime.now()
            logging.info(f"🔄 Starting bot cycle at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"\n🔍 [{current_time.strftime('%H:%M:%S')}] CHECKING FOR NEW MENTIONS...")
            
            # Search for mentions
            mentions = self.search_mentions()
            
            if mentions:
                # Enhanced mention summary
                total_found = len(mentions)
                already_processed = sum(1 for m in mentions if db_queue.is_mention_processed(m["id"]))
                new_to_process = total_found - already_processed
                
                print(f"� MENTION SUMMARY:")
                print(f"   📱 Total mentions found: {total_found}")
                print(f"   ✅ Already processed: {already_processed}")
                print(f"   🆕 New to process: {new_to_process}")
                
                logging.info(f"📥 Found {len(mentions)} mentions to process")
                
                if new_to_process > 0:
                    print(f"\n🔄 PROCESSING QUEUE:")
                
                # Store all mentions in database immediately with post_status=false
                headers = {"Authorization": f"Bearer {BEARER}"}
                processed_count = 0
                
                for i, mention in enumerate(mentions, 1):
                    mention_id = mention["id"]
                    
                    # Skip if already in database
                    if db_queue.is_mention_processed(mention_id):
                        continue
                    
                    processed_count += 1
                    print(f"\n📝 [{processed_count}/{new_to_process}] Processing mention ID: {mention_id}")
                    
                    try:
                        mention_text = mention["text"]
                        conversation_id = mention["conversation_id"]
                        author_id = mention["author_id"]
                        created_at = mention.get("created_at", "")
                        
                        print(f"   💬 Mention: \"{mention_text[:80]}{'...' if len(mention_text) > 80 else ''}\"")
                        
                        # Get original tweet content if this is a reply
                        original_content = None
                        if conversation_id and conversation_id != mention_id:
                            original_content = self.mention_processor.get_original_tweet_content(conversation_id, headers)
                            if original_content:
                                print(f"   📄 Original post: \"{original_content[:60]}{'...' if len(original_content) > 60 else ''}\"")
                        
                        # Extract the actual question
                        question = self.mention_processor.extract_question_from_mention(mention_text, BOT_HANDLE)
                        
                        if question:
                            print(f"   ❓ Extracted question: \"{question[:80]}{'...' if len(question) > 80 else ''}\"")
                        else:
                            print(f"   ❓ No specific question found - will provide general greeting")
                        
                        # Build context question
                        if original_content and question:
                            context_question = f"Original post: '{original_content}'\n\nUser's question/mention: '{question}'"
                        elif original_content and not question:
                            context_question = f"Please explain or comment on this: '{original_content}'"
                        elif question:
                            context_question = question
                        else:
                            context_question = "Hello! How can I help you with Kaspa?"
                        
                        print(f"   🧠 Generating AI response...")
                        
                        # Get AI response
                        ai_response = self.mention_processor.get_ai_response(context_question, conversation_id)
                        
                        # Check if AI response is unavailable
                        if ai_response == "Sorry, I'm currently unavailable.":
                            print(f"   ⚠️ AI service unavailable - skipping mention")
                            logging.info(f"⚠️ Skipping mention {mention_id} - AI response unavailable")
                            # Still mark as processed to avoid re-processing
                            db_queue.add_processed_mention(mention_id)
                            continue
                        
                       
                        
                        
                        print(f"   🤖 AI Response: \"{ai_response[:80]}{'...' if len(ai_response) > 80 else ''}\"")
                        
                        # Store in database with post_status=false
                        mention_data = {
                            "mention_text": mention_text,
                            "author_id": author_id,
                            "created_at": created_at,
                            "original_content": original_content,
                            "extracted_question": question,
                            "context_question": context_question
                        }
                        
                        # Add to database queue (posted=FALSE by default)
                        success = db_queue.add_response(
                            mention_id,
                            ai_response,
                            conversation_id,
                            mention_data,
                            1 if question else 0  # Higher priority for actual questions
                        )
                        
                        if success:
                            print(f"   ✅ Added to posting queue")
                            logging.info(f"✅ Stored mention {mention_id} in database")
                            # Mark as processed
                            db_queue.add_processed_mention(mention_id)
                        else:
                            print(f"   ⚠️ Already in queue")
                            
                    except Exception as e:
                        print(f"   ❌ Error processing mention: {e}")
                        logging.error(f"❌ Error processing mention {mention_id}: {e}")
                        continue
            else:
                logging.info("📭 No new mentions found")
                print("   � No new mentions found this check")
            
            # Process queue (post responses that are not yet posted)
            print(f"\n📤 POSTING FROM QUEUE:")
            self.process_queue()
            
            # Print status and next execution time
            queue_stats = self.response_queue.get_queue_stats()
            posts_remaining = self.rate_tracker.get_posts_remaining()
            
            print(f"\n📋 PROCESSING COMPLETE:")
            print(f"   📝 Queue status: {queue_stats['pending']} pending responses")
            print(f"   📤 Posts remaining today: {posts_remaining}")
            
            # Calculate next execution time
            next_search_time = datetime.fromtimestamp(
                self.rate_tracker.data.get("last_search_time", 0) + SEARCH_RATE_LIMIT
            )
            next_post_time = datetime.fromtimestamp(
                self.rate_tracker.data.get("last_post_reset", 0) + POST_WINDOW
            )
            
            print(f"   ⏰ Next search: {next_search_time.strftime('%H:%M:%S')}")
            print(f"   🔄 Next post reset: {next_post_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 60)
            
            logging.info(f"📊 Status - Queue: {queue_stats['pending']} pending, "
                        f"Posts remaining today: {posts_remaining}")
            logging.info(f"⏰ Next search: {next_search_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"⏰ Next post reset: {next_post_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            logging.error(f"❌ Error in run_cycle: {e}")
    
    def run(self):
        """Main bot loop"""
        print("="*70)
        print("🤖 KASPA TWITTER BOT - OPTIMIZED VERSION")
        print("="*70)
        print(f"📱 Monitoring handle: {BOT_HANDLE}")
        print(f"🔗 Backend endpoint: {BACKEND_URL}")
        print(f"⏰ Search interval: {SEARCH_RATE_LIMIT} seconds")
        print(f"📤 Daily post limit: {POST_RATE_LIMIT} tweets")
        print(f"💾 Using database queue management")
        print("🛑 Press Ctrl+C to stop")
        print("="*70)
        
        logging.info("🚀 Twitter Bot Started")
        logging.info(f"📱 Monitoring: {BOT_HANDLE}")
        logging.info(f"🔗 Backend: {BACKEND_URL}")
        logging.info(f"⏰ Search interval: {SEARCH_RATE_LIMIT} seconds")
        logging.info(f"📤 Daily post limit: {POST_RATE_LIMIT}")
        logging.info("🛑 Press Ctrl+C to stop\n")
        
        # Perform first API call immediately
        logging.info("🔄 Performing initial API call...")
        self.run_cycle()
        
        while True:
            try:
                # Wait before next cycle
                wait_time = SEARCH_RATE_LIMIT
                print(f"\n💤 Sleeping for {wait_time} seconds until next check...")
                print("=" * 70)
                logging.info(f"💤 Sleeping for {wait_time} seconds...")
                time.sleep(wait_time)
                
                # Run next cycle
                self.run_cycle()
                
            except KeyboardInterrupt:
                print("\n" + "="*70)
                print("🛑 Twitter bot stopped by user")
                print("="*70)
                logging.info("\n🛑 Twitter bot stopped by user")
                break
            except Exception as e:
                logging.error(f"💥 Unexpected error: {e}")
                logging.info(f"🔄 Retrying in {SEARCH_RATE_LIMIT//60} minutes...")
                time.sleep(SEARCH_RATE_LIMIT)

def main():
    """Main function"""
    try:
        bot = TwitterBot()
        bot.run()
    except ValueError as e:
        logging.error(f"❌ Configuration error: {e}")
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    main()