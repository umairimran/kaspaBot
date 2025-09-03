
import os, json
from dotenv import load_dotenv
from requests_oauthlib import OAuth1Session
import requests

load_dotenv()

CONSUMER_KEY = os.getenv("TWITTER_API_KEY")      # your Consumer Key
CONSUMER_SECRET = os.getenv("TWITTER_API_SECRET")# your Consumer Secret


# -------- Use saved access token/secret if available, else run PIN-based OAuth --------
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

if not ACCESS_TOKEN or not ACCESS_TOKEN_SECRET:
    # PIN-based OAuth flow
    request_token_url = "https://api.x.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET)
    tokens = oauth.fetch_request_token(request_token_url)  # raises if creds invalid

    resource_owner_key = tokens["oauth_token"]
    resource_owner_secret = tokens["oauth_token_secret"]

    auth_url = oauth.authorization_url("https://api.x.com/oauth/authorize")
    print("Open this URL, approve access, and copy the PIN shown:\n", auth_url)
    verifier = input("Paste PIN here: ").strip()

    access_token_url = "https://api.x.com/oauth/access_token"
    oauth = OAuth1Session(
        CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    final = oauth.fetch_access_token(access_token_url)
    ACCESS_TOKEN = final["oauth_token"]
    ACCESS_TOKEN_SECRET = final["oauth_token_secret"]

    print("\n✅ Got user tokens. Save these in your .env for future runs:")
    print("TWITTER_ACCESS_TOKEN=", ACCESS_TOKEN)
    print("TWITTER_ACCESS_TOKEN_SECRET=", ACCESS_TOKEN_SECRET)


# -------- 4) Ask question, get answer from backend, then post as tweet --------
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/ask")
question = input("Enter your question: ").strip()
try:
    response = requests.post(BACKEND_URL, json={"question": question}, timeout=30)
    response.raise_for_status()
    data = response.json()
    answer = data.get("answer", "No answer received.")
except Exception as e:
    print(f"Error getting answer from backend: {e}")
    answer = "[Backend error]"

tweet_text = f"Q: {question}\nA: {answer}"[:280]

oauth_post = OAuth1Session(
    CONSUMER_KEY,
    client_secret=CONSUMER_SECRET,
    resource_owner_key=ACCESS_TOKEN,
    resource_owner_secret=ACCESS_TOKEN_SECRET,
)
resp = oauth_post.post(
    "https://api.x.com/2/tweets",
    json={"text": tweet_text},
)

if resp.status_code == 201:
    print("✅ Tweet posted successfully!")
else:
    print(f"❌ Post failed: {resp.status_code} {resp.text}")

print("🎉 Posted! Response:\n", json.dumps(resp.json(), indent=2))
