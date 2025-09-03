# Twitter API v2 Output Documentation for Kaspa Bot

## Overview
This document shows the exact JSON response formats for Twitter API v2 endpoints that the Kaspa bot uses with a **paid API plan**. These examples are based on official Twitter API v2 documentation and real-world usage.

## 🔑 Required API Endpoints

### 1. POST /2/tweets (Create Tweet/Reply)
**Purpose**: Post new tweets or reply to existing tweets

#### Request Body - New Tweet
```json
{
  "text": "Q: What is Kaspa's consensus mechanism?\nA: Kaspa uses the GHOSTDAG protocol, which is a novel consensus mechanism that..."
}
```

#### Request Body - Reply to Tweet
```json
{
  "text": "Thanks for asking! Kaspa's GHOSTDAG protocol allows for faster block creation while maintaining security...",
  "reply": {
    "in_reply_to_tweet_id": "1750131234567890123"
  }
}
```

#### Success Response (201 Created)
```json
{
  "data": {
    "id": "1750131234567890124",
    "text": "Q: What is Kaspa's consensus mechanism?\nA: Kaspa uses the GHOSTDAG protocol, which is a novel consensus mechanism that...",
    "edit_history_tweet_ids": [
      "1750131234567890124"
    ]
  }
}
```

#### Error Response (400 Bad Request)
```json
{
  "errors": [
    {
      "message": "Text is required.",
      "parameters": {
        "text": []
      }
    }
  ],
  "title": "Invalid Request",
  "detail": "One or more parameters to your request was invalid.",
  "type": "https://api.twitter.com/2/problems/invalid-request"
}
```

---

### 2. GET /2/tweets/search/recent (Monitor Mentions)
**Purpose**: Search for recent tweets mentioning your bot or specific hashtags

#### Request URL
```
GET https://api.twitter.com/2/tweets/search/recent?query=@YourKaspaBot&max_results=10&tweet.fields=created_at,author_id,conversation_id&user.fields=username,name&expansions=author_id
```

#### Success Response (200 OK)
```json
{
  "data": [
    {
      "id": "1750130000000000001",
      "text": "@YourKaspaBot What is the current block time in Kaspa?",
      "created_at": "2025-09-04T10:30:00.000Z",
      "author_id": "123456789",
      "conversation_id": "1750130000000000001",
      "edit_history_tweet_ids": [
        "1750130000000000001"
      ]
    },
    {
      "id": "1750130000000000002", 
      "text": "@YourKaspaBot How does mining work in Kaspa? #AskKaspa",
      "created_at": "2025-09-04T10:25:00.000Z",
      "author_id": "987654321",
      "conversation_id": "1750130000000000002",
      "edit_history_tweet_ids": [
        "1750130000000000002"
      ]
    }
  ],
  "includes": {
    "users": [
      {
        "id": "123456789",
        "username": "kaspa_enthusiast",
        "name": "Kaspa Fan"
      },
      {
        "id": "987654321",
        "username": "crypto_miner_2024",
        "name": "Crypto Miner"
      }
    ]
  },
  "meta": {
    "newest_id": "1750130000000000001",
    "oldest_id": "1750130000000000002",
    "result_count": 2,
    "next_token": "b26v89c19zqg8o3fogl9yq8yn"
  }
}
```

#### No Results Response (200 OK)
```json
{
  "meta": {
    "result_count": 0
  }
}
```

---

### 3. GET /2/users/by/username/{username} (Get User Info)
**Purpose**: Get user information for mentions and replies

#### Request URL
```
GET https://api.twitter.com/2/users/by/username/kaspa_enthusiast?user.fields=created_at,description,public_metrics
```

#### Success Response (200 OK)
```json
{
  "data": {
    "id": "123456789",
    "username": "kaspa_enthusiast",
    "name": "Kaspa Fan",
    "created_at": "2021-03-15T08:30:00.000Z",
    "description": "Passionate about Kaspa cryptocurrency and blockchain technology",
    "public_metrics": {
      "followers_count": 1250,
      "following_count": 450,
      "tweet_count": 2890,
      "listed_count": 15,
      "like_count": 8920
    }
  }
}
```

---

### 4. GET /2/tweets/{id} (Get Specific Tweet)
**Purpose**: Get details of a specific tweet for context

#### Request URL
```
GET https://api.twitter.com/2/tweets/1750130000000000001?tweet.fields=created_at,author_id,conversation_id,public_metrics&expansions=author_id&user.fields=username,name
```

#### Success Response (200 OK)
```json
{
  "data": {
    "id": "1750130000000000001",
    "text": "@YourKaspaBot What is the current block time in Kaspa?",
    "created_at": "2025-09-04T10:30:00.000Z",
    "author_id": "123456789",
    "conversation_id": "1750130000000000001",
    "public_metrics": {
      "retweet_count": 2,
      "like_count": 8,
      "reply_count": 1,
      "quote_count": 0
    },
    "edit_history_tweet_ids": [
      "1750130000000000001"
    ]
  },
  "includes": {
    "users": [
      {
        "id": "123456789",
        "username": "kaspa_enthusiast",
        "name": "Kaspa Fan"
      }
    ]
  }
}
```

---

## 🚀 Bot Workflow Response Chain

### Complete Interaction Example

#### 1. User mentions bot:
```json
{
  "data": {
    "id": "1750130000000000001",
    "text": "@YourKaspaBot What makes Kaspa different from Bitcoin?",
    "author_id": "123456789"
  }
}
```

#### 2. Bot processes with RAG system:
- Question: "What makes Kaspa different from Bitcoin?"
- RAG Response: "Kaspa differs from Bitcoin primarily in its consensus mechanism..."

#### 3. Bot replies with answer:
```json
{
  "data": {
    "id": "1750130000000000002",
    "text": "Thanks for asking! Kaspa differs from Bitcoin in several key ways:\n\n🔹 Consensus: Uses GHOSTDAG protocol vs Bitcoin's Nakamoto consensus\n🔹 Speed: 1 second block time vs Bitcoin's 10 minutes\n🔹 Scalability: Higher throughput capabilities\n🔹 Energy: More efficient mining\n\nLearn more: kasparchive.com",
    "reply": {
      "in_reply_to_tweet_id": "1750130000000000001"
    }
  }
}
```

---

## 📊 API Rate Limits (Paid Plans)

### Basic Plan ($100/month)
- **POST /2/tweets**: 300 requests per 15-minute window
- **GET /2/tweets/search/recent**: 300 requests per 15-minute window  
- **GET /2/users/by/username**: 900 requests per 15-minute window

### Pro Plan ($5,000/month)
- **POST /2/tweets**: 300 requests per 15-minute window
- **GET /2/tweets/search/recent**: 300 requests per 15-minute window
- **GET /2/users/by/username**: 900 requests per 15-minute window

### Enterprise Plan ($42,000/month)
- **Higher limits**: Custom rate limits negotiated
- **Real-time streaming**: Access to streaming endpoints
- **Advanced features**: Additional functionality

---

## 🔍 Search Query Examples

### Monitor Bot Mentions
```
@YourKaspaBot
```

### Monitor Hashtags
```
#AskKaspa OR #KaspaQuestion
```

### Monitor Keywords
```
kaspa blockchain question
```

### Complex Query
```
(@YourKaspaBot OR #AskKaspa) -is:retweet lang:en
```

---

## ⚠️ Error Handling

### Rate Limit Exceeded (429)
```json
{
  "errors": [
    {
      "message": "Rate limit exceeded",
      "code": 88
    }
  ]
}
```

### Unauthorized (401)
```json
{
  "errors": [
    {
      "message": "Unauthorized",
      "code": 401
    }
  ]
}
```

### Tweet Not Found (404)
```json
{
  "errors": [
    {
      "detail": "Could not find tweet with id: [1750130000000000999].",
      "title": "Not Found Error",
      "resource_type": "tweet",
      "parameter": "id",
      "value": "1750130000000000999",
      "type": "https://api.twitter.com/2/problems/resource-not-found"
    }
  ]
}
```

---

## 💡 Implementation Notes

1. **Authentication**: Use OAuth 2.0 Bearer Token for API calls
2. **Webhook Alternative**: For real-time responses, consider Twitter webhooks
3. **Response Time**: Bot should reply within 1-2 minutes for best engagement
4. **Content Limits**: Twitter allows 280 characters, plan accordingly for long answers
5. **Thread Support**: For longer responses, create tweet threads
6. **Media Support**: API supports image/video attachments with media endpoints

---

## 🔗 Integration with Kaspa RAG System

The bot connects these Twitter API responses with your existing `/ask` endpoint:

```python
# Pseudo-code flow
def handle_mention(mention_tweet):
    question = extract_question(mention_tweet['text'])
    
    # Call your existing RAG endpoint
    response = requests.post('http://localhost:8000/ask', {
        'question': question
    })
    
    # Format and reply via Twitter API
    reply_text = format_answer(response.json()['answer'])
    
    twitter_api.post('/2/tweets', {
        'text': reply_text,
        'reply': {
            'in_reply_to_tweet_id': mention_tweet['id']
        }
    })
```

This creates a seamless integration between Twitter mentions and your Kaspa knowledge base!
