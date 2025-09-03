"""
Context-Aware Twitter Bot for Kaspa
Handles mentions with conversation context for follow-up questions
"""

import os
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

load_dotenv()

class ContextAwareKaspaBot:
    """
    Twitter bot that maintains conversation context for follow-up questions.
    """
    
    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.last_check_time = None
        
        # Twitter API credentials
        self.consumer_key = os.getenv("TWITTER_API_KEY")
        self.consumer_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            raise ValueError("Missing Twitter API credentials in .env file")
        
        # OAuth session for API calls
        self.oauth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )
        
        print("🤖 Context-Aware Kaspa Bot initialized!")
    
    def search_mentions(self, bot_username: str) -> List[Dict]:
        """Search for recent mentions of the bot."""
        query = f"@{bot_username}"
        
        # Add time filter if we have a last check time
        if self.last_check_time:
            query += f" since:{self.last_check_time.strftime('%Y-%m-%d')}"
        
        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": 10,
            "tweet.fields": "created_at,author_id,conversation_id,referenced_tweets",
            "user.fields": "username,name",
            "expansions": "author_id"
        }
        
        response = self.oauth.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"❌ Error searching mentions: {response.status_code} {response.text}")
            return []
    
    def extract_question(self, tweet_text: str, bot_username: str) -> str:
        """Extract the actual question from the tweet."""
        import re
        
        # Remove @mentions
        clean_text = re.sub(r'@\w+\s*', '', tweet_text).strip()
        
        # Remove common Twitter artifacts
        clean_text = re.sub(r'https?://\S+', '', clean_text)  # URLs
        clean_text = re.sub(r'#\w+', '', clean_text)  # Hashtags (optional)
        clean_text = re.sub(r'\s+', ' ', clean_text)  # Multiple spaces
        
        return clean_text.strip()
    
    def get_contextual_answer(self, question: str, conversation_id: str, user_id: str) -> Dict:
        """Get answer from the backend with conversation context."""
        try:
            response = requests.post(
                f"{self.backend_url}/ask",
                json={
                    "question": question,
                    "conversation_id": conversation_id,
                    "user_id": user_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Backend error: {response.status_code} {response.text}")
                return {
                    "answer": "Sorry, I'm having trouble processing your question right now. Please try again later.",
                    "citations": [],
                    "has_context": False
                }
                
        except Exception as e:
            print(f"❌ Error calling backend: {e}")
            return {
                "answer": "Sorry, I'm experiencing technical difficulties. Please try again later.",
                "citations": [],
                "has_context": False
            }
    
    def format_reply(self, answer: str, has_context: bool = False) -> str:
        """Format the answer for Twitter's character limit."""
        
        # Add context indicator if this is a follow-up
        prefix = "💬 " if has_context else "🤖 "
        
        # Calculate available space
        max_length = 280 - len(prefix) - 10  # Leave some buffer
        
        if len(answer) <= max_length:
            return f"{prefix}{answer}"
        
        # Need to truncate - try to break at sentence boundary
        truncated = answer[:max_length]
        
        # Find last sentence end
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        sentence_end = max(last_period, last_exclamation, last_question)
        
        if sentence_end > max_length * 0.7:  # If we can keep most of the content
            return f"{prefix}{truncated[:sentence_end + 1]}"
        else:
            return f"{prefix}{truncated.rstrip()}..."
    
    def reply_to_tweet(self, tweet_id: str, reply_text: str) -> bool:
        """Reply to a tweet."""
        url = "https://api.twitter.com/2/tweets"
        
        data = {
            "text": reply_text,
            "reply": {
                "in_reply_to_tweet_id": tweet_id
            }
        }
        
        response = self.oauth.post(url, json=data)
        
        if response.status_code == 201:
            response_data = response.json()
            tweet_id = response_data.get("data", {}).get("id")
            print(f"✅ Replied successfully! Tweet ID: {tweet_id}")
            return True
        else:
            print(f"❌ Failed to reply: {response.status_code} {response.text}")
            return False
    
    def process_mention(self, tweet: Dict, bot_username: str):
        """Process a single mention with context awareness."""
        try:
            tweet_id = tweet["id"]
            tweet_text = tweet["text"]
            author_id = tweet["author_id"]
            conversation_id = tweet.get("conversation_id", tweet_id)
            
            print(f"\n📬 Processing mention:")
            print(f"   Tweet ID: {tweet_id}")
            print(f"   Author: {author_id}")
            print(f"   Conversation: {conversation_id}")
            print(f"   Text: {tweet_text}")
            
            # Extract the actual question
            question = self.extract_question(tweet_text, bot_username)
            
            if not question:
                print("   ⚠️ No question found in tweet, skipping...")
                return
            
            print(f"   Question: {question}")
            
            # Get contextual answer
            result = self.get_contextual_answer(question, conversation_id, author_id)
            
            answer = result.get("answer", "Sorry, I couldn't process your question.")
            has_context = result.get("has_context", False)
            
            print(f"   Context: {'Yes' if has_context else 'No'}")
            print(f"   Answer: {answer[:100]}...")
            
            # Format and send reply
            reply_text = self.format_reply(answer, has_context)
            
            success = self.reply_to_tweet(tweet_id, reply_text)
            
            if success:
                print("   ✅ Reply sent successfully!")
            else:
                print("   ❌ Failed to send reply")
                
        except Exception as e:
            print(f"   ❌ Error processing mention: {e}")
    
    def run_monitoring_loop(self, bot_username: str, check_interval: int = 60):
        """
        Main monitoring loop that checks for mentions and responds.
        
        Args:
            bot_username: The Twitter username of the bot (without @)
            check_interval: How often to check for mentions (seconds)
        """
        print(f"🚀 Starting monitoring loop for @{bot_username}")
        print(f"   Check interval: {check_interval} seconds")
        print(f"   Backend URL: {self.backend_url}")
        
        while True:
            try:
                print(f"\n🔍 Checking for mentions at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Search for mentions
                mentions = self.search_mentions(bot_username)
                
                if not mentions:
                    print("   No new mentions found")
                else:
                    print(f"   Found {len(mentions)} mention(s)")
                    
                    # Process each mention
                    for mention in mentions:
                        self.process_mention(mention, bot_username)
                        time.sleep(2)  # Small delay between replies
                
                # Update last check time
                self.last_check_time = datetime.now()
                
                # Get conversation stats
                try:
                    stats_response = requests.get(f"{self.backend_url}/conversation_stats")
                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        print(f"   📊 Active conversations: {stats.get('active_conversations', 0)}")
                        print(f"   💬 Total messages: {stats.get('total_messages', 0)}")
                except:
                    pass
                
                print(f"   😴 Sleeping for {check_interval} seconds...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error in monitoring loop: {e}")
                print("   Continuing in 30 seconds...")
                time.sleep(30)


def main():
    """Main function to run the bot."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python twitter_bot_context.py <bot_username>")
        print("Example: python twitter_bot_context.py YourKaspaBot")
        sys.exit(1)
    
    bot_username = sys.argv[1]
    
    # Initialize and run the bot
    bot = ContextAwareKaspaBot()
    bot.run_monitoring_loop(bot_username, check_interval=60)


if __name__ == "__main__":
    main()
