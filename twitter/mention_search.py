#!/usr/bin/env python3
import os
import requests
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
BEARER = os.getenv("TWITTER_BEARER_TOKEN", "AAAAAAAAAAAAAAAAAAAAAL5a3wEAAAAAmWSUwsEx6QeOPY%2BvyBEc73TDHOI%3DNBqVdxAmvsLO0JR2tWsh9OrDNzX61mCmvCtON972IiaE3YTKsc")

# OAuth 1.0a credentials for posting tweets
CONSUMER_KEY = os.getenv("TWITTER_API_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

BOT_HANDLE = os.getenv("BOT_HANDLE")
BACKEND_URL = os.getenv("BACKEND_URL")
CHECK_INTERVAL = 15  # 15 seconds to respect Basic Plan limits (60 requests/15min)
MAX_RETRIES = 3

# Store processed mentions to avoid duplicates
PROCESSED_MENTIONS_FILE = "processed_mentions.json"
INTERACTIONS_LOG_FILE = "twitter_interactions.json"

def load_processed_mentions():
    """Load previously processed mention IDs"""
    try:
        with open(PROCESSED_MENTIONS_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_processed_mentions(processed_ids):
    """Save processed mention IDs"""
    with open(PROCESSED_MENTIONS_FILE, 'w') as f:
        json.dump(list(processed_ids), f)

def save_interaction_to_json(interaction_data):
    """Save interaction details to JSON log file"""
    try:
        # Load existing interactions
        try:
            with open(INTERACTIONS_LOG_FILE, 'r') as f:
                interactions = json.load(f)
        except FileNotFoundError:
            interactions = []
        
        # Add new interaction
        interactions.append(interaction_data)
        
        # Save back to file
        with open(INTERACTIONS_LOG_FILE, 'w') as f:
            json.dump(interactions, f, indent=2, default=str)
            
    except Exception as e:
        print(f"❌ Failed to save interaction to JSON: {e}")

def print_interaction_summary(original_content, mention_text, question, ai_response, success):
    """Print a clean summary of the interaction"""
    print(f"\n{'='*60}")
    print(f"📱 TWITTER INTERACTION SUMMARY")
    print(f"{'='*60}")
    print(f"📄 Original Post: {original_content[:100]}..." if original_content else "📄 Original Post: None")
    print(f"💬 Mention: {mention_text[:100]}...")
    print(f"❓ Question: {question[:100]}...")
    print(f"🤖 AI Response: {ai_response[:100]}...")
    print(f"📤 Reply Status: {'✅ Posted' if success else '❌ Failed'}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

def get_ai_response(question, conversation_id):
    """Get AI response from backend"""
    try:
        response = requests.post(f"{BACKEND_URL}/ask", json={
            "question": question,
            "conversation_id": conversation_id,
            "user_id": "twitter_user"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "Sorry, I couldn't process your question.")
            return answer
        else:
            return "Sorry, I'm experiencing technical difficulties."
    except Exception as e:
        return "Sorry, I'm currently unavailable."

def post_tweet(reply_text, reply_to_id):
    """Post a reply to a tweet using OAuth 1.0a"""
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
        response = auth.post(url, json=payload)
        if response.status_code == 201:
            logging.info(f"✅ Posted reply: {reply_text}")
            return response.json()
        else:
            logging.error(f"❌ Failed to post reply: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"💥 Error posting reply: {e}")
        return None

def post_twitter_reply(tweet_id, response_text):
    """Post a reply to a tweet using the post_tweet function"""
    try:
        result = post_tweet(response_text, tweet_id)
        
        if result:
            tweet_data = result.get("data", {})
            tweet_id = tweet_data.get("id", "unknown")
            return {
                "success": True,
                "reply_id": tweet_id,
                "reply_url": f"https://twitter.com/user/status/{tweet_id}"
            }
        else:
            return {
                "success": False,
                "error": "Failed to post tweet",
                "status_code": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": None
        }

def get_original_tweet_content(conversation_id, headers):
    """Get the content of the original tweet in the conversation"""
    try:
        if conversation_id:
            tweet_url = f"https://api.twitter.com/2/tweets/{conversation_id}"
            response = requests.get(tweet_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                original_text = data.get("data", {}).get("text", "")
                return original_text
            elif response.status_code == 429:
                print(f"⏰ Rate limited while fetching original tweet")
                return None
            else:
                return None
    except Exception as e:
        return None

def extract_question_from_mention(mention_text, bot_handle):
    """Extract the actual question from mention text"""
    # Remove the bot handle and clean up the text
    question = mention_text.replace(bot_handle, "").strip()
    
    # Remove common prefixes and social media artifacts
    prefixes_to_remove = [
        "hey", "hi", "hello", "can you", "could you", "please", 
        "thoughts?", "thoughts on", "what do you think", "opinion on",
        "explain", "tell me about", "what is", "how does"
    ]
    
    # Clean up the question
    words = question.split()
    
    # Remove leading prefixes
    while words and words[0].lower().rstrip('?.,!') in prefixes_to_remove:
        words.pop(0)
    
    cleaned_question = " ".join(words).strip()
    
    # If the cleaned question is too short, it might just be a greeting or mention
    if len(cleaned_question) < 3:
        return ""
    
    return cleaned_question

def check_mentions():
    """Check for new mentions and process them"""
    try:
        # Load previously processed mentions
        processed_mentions = load_processed_mentions()
        
        # Get recent mentions from Twitter API
        mentions_url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": BOT_HANDLE,
            "tweet.fields": "author_id,conversation_id,in_reply_to_user_id,created_at",
            "max_results": 10
        }
        headers = {"Authorization": f"Bearer {BEARER}"}
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Checking for mentions...")
        
        resp = requests.get(mentions_url, params=params, headers=headers, timeout=10)
        
        if resp.status_code == 429:
            # Rate limited - calculate wait time and wait
            reset_time = int(resp.headers.get('x-rate-limit-reset', time.time() + 15))
            wait_time = max(reset_time - int(time.time()), 15)
            print(f"⏰ Rate limited! Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            return
        elif resp.status_code != 200:
            print(f"❌ Error fetching mentions: {resp.status_code}")
            return
        
        data = resp.json()
        mentions = data.get("data", [])
        
        if not mentions:
            print("No mentions found")
            return
        
        new_mentions = [m for m in mentions if m["id"] not in processed_mentions]
        
        if not new_mentions:
            print("No new mentions to process")
            return
        
        print(f"✅ Found {len(new_mentions)} new mentions to process")
        
        for mention in new_mentions:
            try:
                mention_id = mention["id"]
                mention_text = mention["text"]
                conversation_id = mention["conversation_id"]
                author_id = mention["author_id"]
                created_at = mention.get("created_at", "")
                
                # Get original tweet content if this is a reply
                original_content = None
                if conversation_id and conversation_id != mention_id:
                    original_content = get_original_tweet_content(conversation_id, headers)
                
                # Extract the actual question
                question = extract_question_from_mention(mention_text, BOT_HANDLE)
                
                # If we have original content, include it in the context
                if original_content and question:
                    # Combine original content with the mention for better context
                    context_question = f"Original post: '{original_content}'\n\nUser's question/mention: '{question}'"
                elif original_content and not question:
                    # If no specific question but there's original content, ask about it
                    context_question = f"Please explain or comment on this: '{original_content}'"
                elif question:
                    context_question = question
                else:
                    context_question = "Hello! How can I help you with Kaspa?"
                
                # Get AI response using conversation_id for context
                ai_response = get_ai_response(context_question, conversation_id)
                
                # Limit response length for Twitter (280 char limit)
                if len(ai_response) > 250:
                    ai_response = ai_response[:247] + "..."
                
                # Post reply
                reply_result = post_twitter_reply(mention_id, ai_response)
                success = reply_result.get("success", False) if reply_result else False
                
                # Create interaction data for JSON log
                interaction_data = {
                    "timestamp": datetime.now().isoformat(),
                    "mention_id": mention_id,
                    "author_id": author_id,
                    "conversation_id": conversation_id,
                    "created_at": created_at,
                    "original_post": original_content,
                    "mention_text": mention_text,
                    "extracted_question": question,
                    "context_question": context_question,
                    "ai_response": ai_response,
                    "reply_posted": success,
                    "reply_result": reply_result
                }
                
                # Save interaction to JSON
                save_interaction_to_json(interaction_data)
                
                # Print clean summary
                print_interaction_summary(original_content, mention_text, question, ai_response, success)
                
                if success:
                    processed_mentions.add(mention_id)
                
                # Small delay between processing mentions
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing mention {mention['id']}: {e}")
                continue
        
        # Save updated processed mentions
        save_processed_mentions(processed_mentions)
        
    except Exception as e:
        print(f"❌ Error in check_mentions: {e}")

def main():
    """Main monitoring loop"""
    if not BEARER:
        print("❌ Error: TWITTER_BEARER_TOKEN not found")
        return
    
    if not all([CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        print("❌ Error: Missing OAuth 1.0a credentials in environment variables")
        print("Please check your .env file or environment variables.")
        return
    
    print(f"🚀 Twitter Bot Started - Monitoring {BOT_HANDLE}")
    print(f"📱 Backend: {BACKEND_URL}")
    print(f"⏰ Check interval: {CHECK_INTERVAL} seconds")
    print(f"� Logs saved to: {INTERACTIONS_LOG_FILE}")
    print("🛑 Press Ctrl+C to stop\n")
    
    while True:
        try:
            check_mentions()
            print(f"💤 Sleeping for {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 Twitter bot stopped by user")
            break
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            print(f"🔄 Retrying in {CHECK_INTERVAL//60} minutes...")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
