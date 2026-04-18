"""
Ghost Writer - Database Seeder
Populates the database with realistic sample data so you can test
the dashboard without waiting for real RSS fetches and NLP scoring.

Usage: python seed_data.py
"""

import os, sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from database.db_manager import (
    init_db, get_session, Source, Article, ArticleTopic,
    Topic, SentimentScore, EmotionScore, EntitySentiment,
    get_or_create_source, get_or_create_topic,
)

# ─────────────── SAMPLE DATA ───────────────────────────

SOURCES = [
    ("Reuters",          "UK",  "wire"),
    ("BBC",              "UK",  "mainstream"),
    ("CNN",              "US",  "mainstream"),
    ("Fox News",         "US",  "mainstream"),
    ("Al Jazeera",       "QA",  "mainstream"),
    ("The Guardian",     "UK",  "mainstream"),
    ("CNBC",             "US",  "mainstream"),
    ("Associated Press", "US",  "wire"),
]

TOPICS = ["Tesla", "AI", "Climate", "Crypto", "US Politics", "Economy", "Tech Giants", "Geopolitics"]

# Simulated bias profiles per source (sentiment_mean, sentiment_std, subjectivity_mean)
SOURCE_PROFILES = {
    "Reuters":          {"sent_mean":  0.02, "sent_std": 0.15, "subj_mean": 0.25, "emo": "neutral"},
    "BBC":              {"sent_mean":  0.00, "sent_std": 0.18, "subj_mean": 0.30, "emo": "neutral"},
    "CNN":              {"sent_mean": -0.10, "sent_std": 0.25, "subj_mean": 0.45, "emo": "fear"},
    "Fox News":         {"sent_mean":  0.15, "sent_std": 0.30, "subj_mean": 0.55, "emo": "anger"},
    "Al Jazeera":       {"sent_mean": -0.08, "sent_std": 0.20, "subj_mean": 0.35, "emo": "sadness"},
    "The Guardian":     {"sent_mean": -0.12, "sent_std": 0.22, "subj_mean": 0.50, "emo": "fear"},
    "CNBC":             {"sent_mean":  0.10, "sent_std": 0.20, "subj_mean": 0.40, "emo": "joy"},
    "Associated Press": {"sent_mean":  0.01, "sent_std": 0.12, "subj_mean": 0.20, "emo": "neutral"},
}

# Topic-specific sentiment shifts (some sources lean differently per topic)
TOPIC_BIAS = {
    ("Fox News", "Tesla"):       0.20,
    ("Fox News", "Climate"):    -0.25,
    ("CNN", "Tesla"):           -0.15,
    ("CNN", "US Politics"):     -0.10,
    ("CNBC", "Tesla"):           0.15,
    ("CNBC", "Crypto"):          0.10,
    ("The Guardian", "Climate"):  0.05,
    ("The Guardian", "Tech Giants"): -0.20,
    ("Al Jazeera", "Geopolitics"): -0.15,
}

SAMPLE_TITLES = {
    "Tesla": [
        "Tesla Reports Record Quarterly Deliveries",
        "Tesla Faces Regulatory Scrutiny Over Autopilot",
        "Musk Announces New Gigafactory Location",
        "Tesla Stock Volatile Amid Market Uncertainty",
        "Tesla Recall Affects Thousands of Vehicles",
        "Tesla's Energy Division Shows Strong Growth",
        "Analysts Divided on Tesla Valuation",
        "Tesla Expands Charging Network Across Europe",
    ],
    "AI": [
        "New AI Model Breaks Performance Records",
        "Regulators Weigh AI Safety Frameworks",
        "Tech Companies Race to Deploy AI Assistants",
        "AI Job Displacement Fears Grow Among Workers",
        "Breakthrough in AI Medical Diagnosis",
        "AI-Generated Content Raises Copyright Concerns",
        "Universities Adapt Curriculum for AI Era",
        "AI Chips Market Sees Explosive Growth",
    ],
    "Climate": [
        "Global Temperatures Hit New Record High",
        "Renewable Energy Investment Surges Worldwide",
        "Climate Summit Ends With Mixed Results",
        "Extreme Weather Events Linked to Climate Change",
        "Carbon Capture Technology Shows Promise",
        "Fossil Fuel Companies Face Growing Pressure",
        "New Climate Report Warns of Accelerating Change",
        "Electric Vehicle Adoption Accelerates Globally",
    ],
    "Economy": [
        "Federal Reserve Holds Interest Rates Steady",
        "Inflation Shows Signs of Cooling",
        "Job Market Remains Resilient Despite Concerns",
        "Housing Prices Continue Upward Trend",
        "Consumer Spending Beats Expectations",
        "Manufacturing Sector Shows Mixed Signals",
        "Trade Deficit Widens in Latest Report",
        "Small Business Confidence Index Rises",
    ],
    "US Politics": [
        "Congress Debates New Infrastructure Bill",
        "White House Announces Policy Shift",
        "Bipartisan Support Emerges for Tech Regulation",
        "Political Polarization Reaches New Heights",
        "Campaign Fundraising Sets Records",
        "Supreme Court Takes Up Controversial Case",
        "Voter Registration Drives Intensify Nationwide",
        "State Legislatures Push Competing Agendas",
    ],
    "Crypto": [
        "Bitcoin Surges Past Key Resistance Level",
        "Cryptocurrency Exchange Faces Regulatory Action",
        "Ethereum Upgrade Promises Faster Transactions",
        "Institutional Investors Warm to Digital Assets",
        "Crypto Fraud Losses Mount According to FBI",
        "Central Bank Digital Currency Plans Advance",
        "DeFi Protocol Suffers Major Security Breach",
        "Crypto Market Cap Rebounds After Selloff",
    ],
    "Tech Giants": [
        "Apple Unveils Next-Generation Devices",
        "Google Faces Antitrust Lawsuit",
        "Microsoft Cloud Revenue Exceeds Forecasts",
        "Amazon Expands Into Healthcare Market",
        "Meta Pivots Strategy Amid User Decline",
        "Alphabet Reports Strong Ad Revenue Growth",
        "Big Tech Layoffs Continue Across Industry",
        "Tech Giants Invest Billions in Data Centers",
    ],
    "Geopolitics": [
        "Diplomatic Talks Resume Between Major Powers",
        "Trade Tensions Escalate Over Tariff Dispute",
        "Military Buildup Raises Regional Concerns",
        "Humanitarian Crisis Worsens in Conflict Zone",
        "Sanctions Impact Felt Across Global Markets",
        "Alliance Strengthens Defense Cooperation",
        "Territorial Dispute Enters New Phase",
        "Peace Negotiations Show Signs of Progress",
    ],
}

EMOTION_PROFILES = {
    "neutral":  {"joy": 0.05, "anger": 0.05, "fear": 0.05, "sadness": 0.05, "disgust": 0.02, "surprise": 0.03, "neutral": 0.75},
    "joy":      {"joy": 0.40, "anger": 0.05, "fear": 0.05, "sadness": 0.05, "disgust": 0.02, "surprise": 0.10, "neutral": 0.33},
    "anger":    {"joy": 0.05, "anger": 0.35, "fear": 0.10, "sadness": 0.10, "disgust": 0.15, "surprise": 0.05, "neutral": 0.20},
    "fear":     {"joy": 0.03, "anger": 0.10, "fear": 0.40, "sadness": 0.15, "disgust": 0.05, "surprise": 0.07, "neutral": 0.20},
    "sadness":  {"joy": 0.03, "anger": 0.08, "fear": 0.12, "sadness": 0.40, "disgust": 0.05, "surprise": 0.02, "neutral": 0.30},
}

ENTITIES_BY_TOPIC = {
    "Tesla":       [("Tesla", "ORG"), ("Elon Musk", "PERSON"), ("SEC", "ORG")],
    "AI":          [("OpenAI", "ORG"), ("Google", "ORG"), ("Microsoft", "ORG")],
    "Climate":     [("United Nations", "ORG"), ("EPA", "ORG"), ("China", "GPE")],
    "Economy":     [("Federal Reserve", "ORG"), ("Wall Street", "ORG"), ("US", "GPE")],
    "US Politics": [("Congress", "ORG"), ("White House", "ORG"), ("Supreme Court", "ORG")],
    "Crypto":      [("Bitcoin", "PRODUCT"), ("Ethereum", "PRODUCT"), ("SEC", "ORG")],
    "Tech Giants": [("Apple", "ORG"), ("Google", "ORG"), ("Amazon", "ORG"), ("Meta", "ORG")],
    "Geopolitics": [("NATO", "ORG"), ("China", "GPE"), ("Russia", "GPE"), ("US", "GPE")],
}


def clamp(val, lo=-1.0, hi=1.0):
    return max(lo, min(hi, val))


def seed_database(num_days: int = 60, articles_per_source_per_topic: int = 3):
    """Generate and insert realistic sample data."""

    init_db()
    print("[SEED] Starting database seeding...\n")

    total_articles = 0
    now = datetime.utcnow()

    with get_session() as session:
        # Create sources
        for name, country, mtype in SOURCES:
            get_or_create_source(session, name, country, mtype)

        # Create topics
        for topic in TOPICS:
            get_or_create_topic(session, topic)

        session.flush()

        # Generate articles
        for source_name, country, mtype in SOURCES:
            source = session.query(Source).filter_by(name=source_name).first()
            profile = SOURCE_PROFILES[source_name]

            for topic_name in TOPICS:
                topic = session.query(Topic).filter_by(name=topic_name).first()
                titles = SAMPLE_TITLES.get(topic_name, [])
                topic_shift = TOPIC_BIAS.get((source_name, topic_name), 0)

                for i in range(articles_per_source_per_topic):
                    # Random date within the range
                    days_ago = random.randint(0, num_days)
                    pub_date = now - timedelta(
                        days=days_ago,
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59),
                    )

                    title = random.choice(titles) if titles else f"{topic_name} News Update"
                    url = (f"https://example.com/{source_name.lower().replace(' ', '-')}/"
                           f"{topic_name.lower()}/{pub_date.strftime('%Y%m%d')}-{i}-{random.randint(1000,9999)}")

                    body = (f"This is a sample article from {source_name} about {topic_name}. "
                            f"{title}. The article contains analysis and reporting on recent developments.")

                    article = Article(
                        source_id=source.id,
                        title=title,
                        description=title,
                        full_text=body,
                        url=url,
                        published_at=pub_date,
                        word_count=random.randint(200, 1500),
                    )
                    session.add(article)
                    session.flush()

                    # Link topic
                    at = ArticleTopic(
                        article_id=article.id,
                        topic_id=topic.id,
                        relevance_score=round(random.uniform(2.0, 10.0), 2),
                    )
                    session.add(at)

                    # ── Sentiment Score ──
                    vader = clamp(random.gauss(
                        profile["sent_mean"] + topic_shift,
                        profile["sent_std"]
                    ))
                    roberta_score = abs(vader) + random.uniform(0, 0.3)
                    roberta_score = min(roberta_score, 1.0)

                    if vader > 0.1:
                        roberta_label = "positive"
                    elif vader < -0.1:
                        roberta_label = "negative"
                    else:
                        roberta_label = "neutral"

                    subj = clamp(
                        random.gauss(profile["subj_mean"], 0.12),
                        0, 1
                    )

                    ss = SentimentScore(
                        article_id=article.id,
                        roberta_label=roberta_label,
                        roberta_score=round(roberta_score, 4),
                        vader_compound=round(vader, 4),
                        vader_positive=round(max(0, vader) * 0.8 + random.uniform(0, 0.1), 4),
                        vader_negative=round(max(0, -vader) * 0.8 + random.uniform(0, 0.1), 4),
                        vader_neutral=round(random.uniform(0.3, 0.7), 4),
                        textblob_polarity=round(clamp(vader + random.gauss(0, 0.1)), 4),
                        textblob_subjectivity=round(subj, 4),
                    )
                    session.add(ss)

                    # ── Emotion Score ──
                    emo_profile = EMOTION_PROFILES.get(profile["emo"], EMOTION_PROFILES["neutral"])
                    emotions = {}
                    for emo, base_val in emo_profile.items():
                        emotions[emo] = round(clamp(base_val + random.gauss(0, 0.05), 0, 1), 4)

                    dominant = max(emotions, key=emotions.get)
                    es = EmotionScore(
                        article_id=article.id,
                        dominant_emotion=dominant,
                        **emotions,
                    )
                    session.add(es)

                    # ── Entity Sentiments ──
                    entities = ENTITIES_BY_TOPIC.get(topic_name, [])
                    for ent_text, ent_label in random.sample(entities, min(2, len(entities))):
                        ent_vader = clamp(vader + random.gauss(0, 0.15))
                        if ent_vader > 0.1:
                            ent_label_s = "positive"
                        elif ent_vader < -0.1:
                            ent_label_s = "negative"
                        else:
                            ent_label_s = "neutral"

                        ent_sent = EntitySentiment(
                            article_id=article.id,
                            entity_text=ent_text,
                            entity_label=ent_label,
                            sentiment_label=ent_label_s,
                            sentiment_score=round(abs(ent_vader) + random.uniform(0, 0.2), 4),
                            context_snippet=f"...{ent_text} was mentioned in the context of {topic_name}...",
                        )
                        session.add(ent_sent)

                    total_articles += 1

        session.commit()

    print(f"\n[SEED] Done! Inserted {total_articles} articles with full analysis data.")
    print(f"[SEED] Sources: {len(SOURCES)} | Topics: {len(TOPICS)}")
    print(f"[SEED] Date range: last {num_days} days")
    print(f"\n  Now run: streamlit run dashboard.py")


if __name__ == "__main__":
    seed_database()
