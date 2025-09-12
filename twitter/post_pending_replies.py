#!/usr/bin/env python3
"""
Twitter Reply Bot - Posts AI responses from twitter_interactions.json

This script reads the twitter_interactions.json file and posts replies
for any interactions that haven't been posted yet (reply_posted: false).
Uses PIN-based OAuth authentication instead of stored tokens.
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OAuth 1.0a credentials - only need consumer key/secret
CONSUMER_KEY = os.getenv("TWITTER_API_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_API_SECRET")

INTERACTIONS_LOG_FILE = "twitter_interactions.json"

def get_oauth_tokens():
    """Get OAuth tokens using PIN-based authentication"""
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        logging.error("❌ Missing TWITTER_API_KEY or TWITTER_API_SECRET in .env file")
        return None, None
    
    try:
        # Step 1: Get request token
        print("🔐 Starting PIN-based OAuth authentication...")
        request_token_url = "https://api.x.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
        oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET)
        tokens = oauth.fetch_request_token(request_token_url)

        resource_owner_key = tokens["oauth_token"]
        resource_owner_secret = tokens["oauth_token_secret"]

        # Step 2: User authorization
        auth_url = oauth.authorization_url("https://api.x.com/oauth/authorize")
        print(f"\n🌐 Please open this URL in your browser:")
        print(f"   {auth_url}")
        print(f"\n📝 Approve access and copy the PIN shown")
        verifier = input("🔢 Paste PIN here: ").strip()

        # Step 3: Get access token
        access_token_url = "https://api.x.com/oauth/access_token"
        oauth = OAuth1Session(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        final = oauth.fetch_access_token(access_token_url)
        access_token = final["oauth_token"]
        access_token_secret = final["oauth_token_secret"]

        print("✅ OAuth authentication successful!")
        print(f"💡 Tip: You can save these tokens in your .env file for future use:")
        print(f"   TWITTER_ACCESS_TOKEN={access_token}")
        print(f"   TWITTER_ACCESS_TOKEN_SECRET={access_token_secret}")
        
        return access_token, access_token_secret
        
    except Exception as e:
        logging.error(f"❌ OAuth authentication failed: {e}")
        return None, None

def post_tweet(reply_text, reply_to_id, access_token, access_token_secret):
    """Post a reply to a tweet using OAuth 1.0a with provided tokens"""
    try:
        url = "https://api.twitter.com/2/tweets"
        payload = {
            "text": reply_text,
            "reply": {"in_reply_to_tweet_id": reply_to_id}
        }
        auth = OAuth1Session(
            CONSUMER_KEY,
            client_secret=CONSUMER_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        response = auth.post(url, json=payload)
        if response.status_code == 201:
            logging.info(f"✅ Posted reply: {reply_text[:50]}...")
            return response.json()
        else:
            logging.error(f"❌ Failed to post reply: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"💥 Error posting reply: {e}")
        return None

def load_interactions():
    """Load interactions from JSON file"""
    try:
        with open(INTERACTIONS_LOG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"❌ File not found: {INTERACTIONS_LOG_FILE}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"❌ Invalid JSON in {INTERACTIONS_LOG_FILE}: {e}")
        return []

def save_interactions(interactions):
    """Save updated interactions back to JSON file"""
    try:
        with open(INTERACTIONS_LOG_FILE, 'w') as f:
            json.dump(interactions, f, indent=2, default=str)
        logging.info(f"💾 Updated interactions saved to {INTERACTIONS_LOG_FILE}")
    except Exception as e:
        logging.error(f"❌ Failed to save interactions: {e}")

def post_pending_replies():
    """Process all interactions and post replies for unpublished ones"""
    # Check credentials
    if not CONSUMER_KEY or not CONSUMER_SECRET:
        logging.error("❌ Missing TWITTER_API_KEY or TWITTER_API_SECRET in .env file")
        return
    
    # Get OAuth tokens using PIN authentication
    access_token, access_token_secret = get_oauth_tokens()
    if not access_token or not access_token_secret:
        logging.error("❌ Failed to get OAuth tokens")
        return
    
    # Load interactions
    interactions = load_interactions()
    if not interactions:
        logging.info("📭 No interactions found to process")
        return
    
    # Find interactions that need replies posted
    pending_replies = [i for i in interactions if not i.get("reply_posted", False)]
    
    if not pending_replies:
        logging.info("✅ All interactions already have replies posted")
        return
    
    logging.info(f"📤 Found {len(pending_replies)} pending replies to post")
    
    # Track statistics
    posted_count = 0
    failed_count = 0
    
    # Process each pending reply
    for interaction in interactions:
        if interaction.get("reply_posted", False):
            continue  # Skip already posted
        
        mention_id = interaction.get("mention_id")
        ai_response = interaction.get("ai_response")
        
        if not mention_id or not ai_response:
            logging.warning(f"⚠️ Skipping interaction with missing data: {interaction.get('timestamp', 'unknown')}")
            failed_count += 1
            continue
        
        # Limit response length for Twitter (280 char limit)
        if len(ai_response) > 250:
            ai_response = ai_response[:247] + "..."
        
        logging.info(f"📱 Posting reply to mention {mention_id}...")
        
        # Post the reply
        result = post_tweet(ai_response, mention_id, access_token, access_token_secret)
        
        if result:
            # Update interaction with success
            interaction["reply_posted"] = True
            interaction["reply_result"] = {
                "success": True,
                "reply_id": result.get("data", {}).get("id"),
                "posted_at": datetime.now().isoformat()
            }
            posted_count += 1
            logging.info(f"✅ Successfully posted reply for mention {mention_id}")
        else:
            # Update interaction with failure
            interaction["reply_posted"] = False
            interaction["reply_result"] = {
                "success": False,
                "error": "Failed to post tweet",
                "attempted_at": datetime.now().isoformat()
            }
            failed_count += 1
            logging.error(f"❌ Failed to post reply for mention {mention_id}")
    
    # Save updated interactions
    save_interactions(interactions)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 REPLY POSTING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successfully posted: {posted_count}")
    print(f"❌ Failed to post: {failed_count}")
    print(f"📝 Total processed: {len(pending_replies)}")
    print(f"💾 Results saved to: {INTERACTIONS_LOG_FILE}")
    print(f"{'='*60}\n")

def main():
    """Main function"""
    print("🚀 Twitter Reply Bot - Posting AI Responses")
    print("=" * 50)
    
    try:
        post_pending_replies()
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
    except Exception as e:
        logging.error(f"💥 Unexpected error: {e}")

if __name__ == "__main__":
    main()
