"""
Ghost Writer - Configuration
Central config for RSS feeds, database, NLP models, and topic keywords.
"""

import os

# ─────────────────────────── DATABASE ───────────────────────────
# Switch between PostgreSQL and SQLite
# Set DATABASE_URL env var for PostgreSQL, otherwise falls back to SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///ghost_writer.db"  # default: local SQLite file
)

# ─────────────────────────── RSS FEEDS ──────────────────────────
# name → list of RSS feed URLs
RSS_FEEDS = {
    "Reuters": [
        "https://feeds.reuters.com/reuters/topNews",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.reuters.com/reuters/technologyNews",
    ],
    "BBC": [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
    ],
    "CNN": [
        "http://rss.cnn.com/rss/edition.rss",
        "http://rss.cnn.com/rss/money_latest.rss",
        "http://rss.cnn.com/rss/edition_technology.rss",
    ],
    "Fox News": [
        "https://moxie.foxnews.com/google-publisher/latest.xml",
        "https://moxie.foxnews.com/google-publisher/politics.xml",
        "https://moxie.foxnews.com/google-publisher/tech.xml",
    ],
    "Al Jazeera": [
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "The Guardian": [
        "https://www.theguardian.com/world/rss",
        "https://www.theguardian.com/business/rss",
        "https://www.theguardian.com/technology/rss",
    ],
    "CNBC": [
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
    ],
    "Associated Press": [
        "https://rsshub.app/apnews/topics/apf-topnews",
    ],
}

# ─────────────────────────── TOPIC KEYWORDS ─────────────────────
# Each topic maps to a list of keywords (case-insensitive matching)
TOPIC_KEYWORDS = {
    "Tesla":        ["tesla", "tsla", "elon musk", "cybertruck", "model 3", "model y"],
    "AI":           ["artificial intelligence", "openai", "chatgpt", "gemini", "claude", "llm", "machine learning", "deep learning"],
    "Climate":      ["climate change", "global warming", "carbon emissions", "renewable energy", "fossil fuel", "net zero"],
    "Crypto":       ["bitcoin", "btc", "ethereum", "cryptocurrency", "crypto", "blockchain"],
    "US Politics":  ["white house", "congress", "senate", "republican", "democrat", "gop", "biden", "trump"],
    "Economy":      ["inflation", "federal reserve", "interest rate", "gdp", "recession", "unemployment", "stock market"],
    "Tech Giants":  ["apple", "google", "microsoft", "amazon", "meta", "facebook", "alphabet"],
    "Geopolitics":  ["ukraine", "russia", "china", "taiwan", "nato", "middle east", "gaza", "israel"],
}

# ─────────────────────────── NLP MODELS ─────────────────────────
SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
EMOTION_MODEL   = "j-hartmann/emotion-english-distilroberta-base"
SPACY_MODEL     = "en_core_web_sm"   # for NER; use en_core_web_trf for accuracy

# ─────────────────────────── SCHEDULER ──────────────────────────
FETCH_INTERVAL_HOURS = 6   # how often to run the full pipeline
MAX_ARTICLES_PER_FEED = 25  # limit per RSS feed per fetch cycle

# ─────────────────────────── DASHBOARD ──────────────────────────
MIN_ARTICLES_FOR_STATS = 5  # minimum article count to show a source in charts
