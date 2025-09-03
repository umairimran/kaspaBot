# Twitter Integration for Kaspa RAG Chatbot

## Overview
This guide explains how to integrate your Kaspa RAG chatbot with Twitter to automatically respond to user questions. The bot can monitor mentions, reply to tweets, and provide intelligent answers using your knowledge base.

## 🎯 Integration Options

### Option 1: Mention-Based Responses
- Monitor Twitter mentions of your bot account
- Automatically reply with relevant answers
- Users tweet: "@YourKaspaBot What is Kaspa's consensus mechanism?"
- Bot replies with accurate information from your knowledge base

### Option 2: Hashtag Monitoring
- Monitor specific hashtags like #AskKaspa, #KaspaQuestion
- Respond to tweets containing these hashtags
- Broader reach than just mentions

### Option 3: DM Responses
- Users send direct messages with questions
- Bot responds privately with detailed answers
- More private interaction method

## 🔧 Technical Implementation

### Current Setup
Your current setup includes:
- ✅ Twitter API credentials in `.env`
- ✅ `post_to_twitter_args.py` script for posting
- ✅ RAG chatbot with 369 embeddings
- ✅ `/ask` endpoint for questions
- ✅ Qdrant vector database

### Required Components

#### 1. Twitter API Access
```python
# Required Twitter API v2 endpoints:
- GET /2/tweets/search/recent  # Monitor mentions/hashtags
- POST /2/tweets              # Reply to tweets
- GET /2/users/by/username    # Get user info
- POST /2/direct_messages     # Send DMs (optional)
```

#### 2. Twitter Bot Script
```python
# twitter/twitter_bot.py
import tweepy
import time
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

class KaspaTwitterBot:
    def __init__(self):
        self.api = self.setup_twitter_api()
        self.backend_url = "http://localhost:8000"
        self.last_check = datetime.now()
        
    def setup_twitter_api(self):
        # Setup Twitter API v2 client
        pass
        
    def monitor_mentions(self):
        # Check for new mentions
        pass
        
    def process_question(self, tweet_text):
        # Send to RAG backend
        pass
        
    def reply_to_tweet(self, original_tweet_id, response):
        # Reply with answer
        pass
```

## 📊 Twitter API Pricing & Limitations

### Free Tier (Basic)
**Cost:** $0/month
**Limitations:**
- ⚠️ **Tweet Cap:** 1,500 tweets/month
- ⚠️ **Read Limit:** 10,000 tweets/month for monitoring
- ⚠️ **Rate Limits:** 300 requests/15min window
- ⚠️ **No Real-time Streaming**
- ⚠️ **Limited to 3 apps**

**Reality Check:** Free tier is insufficient for active bot responses

### Pro Tier
**Cost:** $100/month
**Benefits:**
- ✅ **Tweet Cap:** 3,000 tweets/month
- ✅ **Read Limit:** 300,000 tweets/month
- ✅ **Rate Limits:** 300 requests/15min (same as free)
- ✅ **Real-time Filtered Stream** (limited)
- ✅ **10 apps allowed**

**Suitable for:** Small to medium bot activity

### Enterprise
**Cost:** $42,000/month
**Benefits:**
- ✅ **Unlimited tweets**
- ✅ **Unlimited reads**
- ✅ **Higher rate limits**
- ✅ **Full real-time streaming**
- ✅ **Premium support**

**Suitable for:** Large-scale commercial bots

## 💰 Cost Analysis for Kaspa Bot

### Scenario 1: Light Activity
- **Responses:** 50 tweets/day (1,500/month)
- **Monitoring:** Check mentions every 5 minutes
- **Cost:** $100/month (Pro tier)
- **OpenAI Cost:** ~$20/month (estimate)
- **Total:** ~$120/month

### Scenario 2: Moderate Activity
- **Responses:** 100 tweets/day (3,000/month)
- **Monitoring:** Real-time mentions + hashtags
- **Cost:** $100/month (Pro tier at limit)
- **OpenAI Cost:** ~$40/month
- **Total:** ~$140/month

### Scenario 3: High Activity
- **Responses:** 200+ tweets/day
- **Monitoring:** Comprehensive hashtag monitoring
- **Cost:** $42,000/month (Enterprise required)
- **OpenAI Cost:** ~$80/month
- **Total:** ~$42,080/month

## 🚀 Implementation Steps

### Step 1: Upgrade Twitter API
1. Apply for Pro tier ($100/month)
2. Get approved (can take 1-7 days)
3. Update API credentials

### Step 2: Create Twitter Bot
```bash
# Install required packages
pip install tweepy schedule

# Create bot script
touch twitter/twitter_bot.py
```

### Step 3: Bot Features
```python
# Core features to implement:
1. Mention monitoring
2. Question extraction
3. RAG integration
4. Response posting
5. Rate limit handling
6. Error logging
```

### Step 4: Deployment
```bash
# Run bot continuously
python twitter/twitter_bot.py

# Or use systemd/cron for production
```

## ⚡ Quick Start (Free Tier Test)

For testing with free tier limitations:

```python
# twitter/simple_bot.py
import tweepy
import requests
import time

def check_mentions_once():
    \"\"\"Check mentions once and respond to latest\"\"\"
    # Get mentions (limited to 1,500/month)
    mentions = api.mentions_timeline(count=5)
    
    for mention in mentions:
        if should_respond(mention):
            question = extract_question(mention.text)
            answer = get_kaspa_answer(question)
            reply_to_tweet(mention.id, answer)
            break  # Only respond to one to save quota

def get_kaspa_answer(question):
    response = requests.post('http://localhost:8000/ask', 
                           json={'question': question})
    return response.json()['answer']

# Run once every hour to stay within limits
while True:
    check_mentions_once()
    time.sleep(3600)  # Wait 1 hour
```

## 🛡️ Best Practices

### Rate Limit Management
```python
def respect_rate_limits():
    # Twitter API v2 limits: 300 requests/15min
    # Space requests: 1 every 3 seconds minimum
    time.sleep(3)
```

### Content Filtering
```python
def should_respond(tweet):
    # Only respond to genuine questions
    # Avoid spam, promotional content
    # Check if already responded
    pass
```

### Error Handling
```python
try:
    response = api.create_tweet(text=reply_text, 
                               in_reply_to_tweet_id=original_id)
except tweepy.TooManyRequests:
    # Handle rate limit
    time.sleep(900)  # Wait 15 minutes
except tweepy.Forbidden:
    # Handle permission errors
    log_error("Cannot reply to this tweet")
```

## 📋 Recommended Approach

### Phase 1: Testing (Free Tier)
1. Start with free tier for testing
2. Respond to 1-2 mentions per day manually
3. Test question extraction and answering
4. **Duration:** 1-2 weeks
5. **Cost:** $0 + OpenAI usage (~$5)

### Phase 2: Limited Auto-Response (Pro Tier)
1. Upgrade to Pro tier ($100/month)
2. Auto-respond to mentions (50/day max)
3. Monitor performance and user feedback
4. **Duration:** 1-3 months
5. **Cost:** $100/month + OpenAI (~$20/month)

### Phase 3: Full Integration (Pro/Enterprise)
1. Scale based on demand
2. Add hashtag monitoring
3. Implement advanced features
4. **Cost:** $100-$42,000/month depending on scale

## 🔗 Integration Commands

Create the Twitter bot integration:

```bash
# 1. Install dependencies
pip install tweepy schedule python-dotenv

# 2. Create bot script
python twitter/create_twitter_bot.py

# 3. Test with your credentials
python twitter/test_twitter_connection.py

# 4. Run the bot
python twitter/twitter_bot.py
```

## ☁️ Deployment Options

### Option 1: VPS/Cloud Server (Recommended)
**Best for:** 24/7 bot operation, full control

#### Popular Providers:
- **DigitalOcean Droplet:** $12-48/month
- **AWS EC2:** $10-50/month
- **Google Cloud Compute:** $13-52/month
- **Linode:** $12-48/month
- **Vultr:** $6-24/month

#### Setup Steps:
```bash
# 1. Create Ubuntu 22.04 server (2GB RAM minimum)
# 2. Install requirements
sudo apt update
sudo apt install python3 python3-pip docker.io
pip3 install -r requirements.txt

# 3. Install Qdrant
sudo docker run -d -p 6333:6333 \
  -v /opt/qdrant:/qdrant/storage \
  qdrant/qdrant

# 4. Upload your project
scp -r KaspaArchieve user@your-server:/home/user/

# 5. Setup systemd services
sudo systemctl enable kaspa-bot
sudo systemctl start kaspa-bot
```

#### Cost Estimate:
- **Server:** $12-48/month
- **Twitter API:** $100/month (Pro)
- **OpenAI:** $20-40/month
- **Total:** $132-188/month

### Option 2: Docker + Cloud Run (Serverless)
**Best for:** Cost optimization, auto-scaling

#### Google Cloud Run:
```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "twitter/twitter_bot.py"]
```

```bash
# Deploy to Cloud Run
gcloud run deploy kaspa-bot --source . --region us-central1
```

#### Cost Estimate:
- **Cloud Run:** $5-20/month (based on usage)
- **Qdrant on Cloud:** $29-99/month
- **Twitter API:** $100/month
- **OpenAI:** $20-40/month
- **Total:** $154-259/month

### Option 3: Railway (Easiest)
**Best for:** Quick deployment, beginner-friendly

```bash
# 1. Connect GitHub repo to Railway
# 2. Add environment variables
# 3. Deploy automatically
```

#### Cost Estimate:
- **Railway:** $5-20/month
- **External Qdrant:** $29-99/month  
- **Twitter API:** $100/month
- **OpenAI:** $20-40/month
- **Total:** $154-259/month

### Option 4: Heroku
**Best for:** Simplicity (but more expensive)

```bash
# Create Heroku app
heroku create kaspa-twitter-bot

# Add environment variables
heroku config:set OPENAI_API_KEY=your_key
heroku config:set TWITTER_API_KEY=your_key

# Deploy
git push heroku main
```

#### Cost Estimate:
- **Heroku Dyno:** $25-250/month
- **Heroku Postgres:** $9-50/month (if needed)
- **External Qdrant:** $29-99/month
- **Twitter API:** $100/month
- **OpenAI:** $20-40/month
- **Total:** $183-539/month

### Option 5: Home Server/Raspberry Pi
**Best for:** Learning, low cost (not recommended for production)

#### Requirements:
- Raspberry Pi 4 (4GB+ RAM)
- Stable internet connection
- Dynamic DNS service

#### Cost Estimate:
- **Hardware:** $100-200 (one-time)
- **Electricity:** $5-10/month
- **Internet:** Existing
- **Twitter API:** $100/month
- **OpenAI:** $20-40/month
- **Total:** $125-150/month (after hardware)

## 🏆 Recommended Deployment Strategy

### Phase 1: Development & Testing
**Platform:** Local development + ngrok for testing
```bash
# Test locally with ngrok
ngrok http 8000
# Use ngrok URL for webhook testing
```
**Cost:** $0/month (free tier testing)

### Phase 2: Production Deployment
**Platform:** DigitalOcean Droplet ($24/month) + Docker
**Reason:** 
- ✅ Full control over environment
- ✅ Can run Qdrant locally (saves $29-99/month)
- ✅ Reliable uptime
- ✅ Easy to scale
- ✅ SSH access for debugging

### Phase 3: Scale-Up (if needed)
**Platform:** Google Cloud Run + Managed Qdrant
**Reason:**
- ✅ Auto-scaling based on demand
- ✅ Pay only for usage
- ✅ Managed infrastructure
- ✅ Global deployment

## 🚀 Production Setup Guide

### DigitalOcean Deployment (Recommended)

#### 1. Create Droplet
```bash
# Create Ubuntu 22.04 droplet (4GB RAM, 2 CPUs)
# Cost: $24/month
```

#### 2. Server Setup
```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Python
apt install python3-pip python3-venv git -y
```

#### 3. Deploy Application
```bash
# Clone your repo
git clone https://github.com/yourusername/KaspaArchieve.git
cd KaspaArchieve

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start Qdrant
docker run -d --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Migrate embeddings
cd backend/db
python qdrant_utils.py migrate
```

#### 4. Create Systemd Services
```ini
# /etc/systemd/system/kaspa-backend.service
[Unit]
Description=Kaspa RAG Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/KaspaArchieve/backend
Environment=PATH=/root/KaspaArchieve/venv/bin
ExecStart=/root/KaspaArchieve/venv/bin/python -m uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/kaspa-twitter-bot.service
[Unit]
Description=Kaspa Twitter Bot
After=network.target kaspa-backend.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/KaspaArchieve/twitter
Environment=PATH=/root/KaspaArchieve/venv/bin
ExecStart=/root/KaspaArchieve/venv/bin/python twitter_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 5. Start Services
```bash
# Enable and start services
systemctl enable kaspa-backend kaspa-twitter-bot
systemctl start kaspa-backend kaspa-twitter-bot

# Check status
systemctl status kaspa-backend
systemctl status kaspa-twitter-bot
```

#### 6. Setup Nginx (Optional)
```nginx
# /etc/nginx/sites-available/kaspa-api
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Total Cost Breakdown (Recommended Setup)

### Monthly Costs:
- **DigitalOcean Droplet (4GB):** $24/month
- **Twitter API Pro:** $100/month
- **OpenAI API:** $30/month (estimated)
- **Domain (optional):** $1/month
- **SSL Certificate:** $0 (Let's Encrypt)

### **Total: ~$155/month**

### One-time Costs:
- **Development time:** Your time
- **Domain registration:** $10-15/year
- **Setup:** 4-6 hours

## 🔒 Security Considerations

### Environment Variables
```bash
# Create .env file on server
OPENAI_API_KEY=your_key
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_TOKEN_SECRET=your_token_secret
```

### Firewall Setup
```bash
# Setup UFW firewall
ufw enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 8000  # For API access
```

### SSL Certificate
```bash
# Install Certbot for free SSL
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

## 📝 Next Steps

1. **Decision:** Choose your budget tier (Free test vs $100 Pro vs $42K Enterprise)
2. **Apply:** Apply for Twitter API Pro access if needed
3. **Develop:** Create the monitoring and response bot
4. **Test:** Start with limited responses
5. **Scale:** Increase activity based on results

Would you like me to create the actual bot implementation code for any of these approaches?
