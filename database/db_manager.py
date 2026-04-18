"""
Ghost Writer - Database Manager
Handles connections, table creation, and all CRUD operations.
Works with both PostgreSQL and SQLite via SQLAlchemy.
"""

import os
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import (
    create_engine, text, Column, Integer, Float, String, Text,
    DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATABASE_URL

# ─────────────────────── ENGINE SETUP ───────────────────
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # reconnect stale connections
    # SQLite needs check_same_thread=False for multi-thread access
    **({"connect_args": {"check_same_thread": False}} if "sqlite" in DATABASE_URL else {})
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ─────────────────────── ORM MODELS ─────────────────────

class Source(Base):
    __tablename__ = "sources"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String, nullable=False, unique=True)
    country    = Column(String)
    media_type = Column(String, default="mainstream")
    created_at = Column(DateTime, default=datetime.utcnow)

    articles   = relationship("Article", back_populates="source")


class Topic(Base):
    __tablename__ = "topics"
    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)


class ArticleTopic(Base):
    __tablename__ = "article_topics"
    article_id      = Column(Integer, ForeignKey("articles.id"), primary_key=True)
    topic_id        = Column(Integer, ForeignKey("topics.id"), primary_key=True)
    relevance_score = Column(Float, default=1.0)


class Article(Base):
    __tablename__ = "articles"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    source_id    = Column(Integer, ForeignKey("sources.id"), nullable=False)
    title        = Column(Text, nullable=False)
    description  = Column(Text)
    full_text    = Column(Text)
    url          = Column(String, unique=True, nullable=False)
    author       = Column(String)
    published_at = Column(DateTime)
    fetched_at   = Column(DateTime, default=datetime.utcnow)
    word_count   = Column(Integer, default=0)

    source            = relationship("Source", back_populates="articles")
    sentiment_scores  = relationship("SentimentScore", back_populates="article", uselist=False)
    emotion_scores    = relationship("EmotionScore", back_populates="article", uselist=False)
    entity_sentiments = relationship("EntitySentiment", back_populates="article")


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"
    id                    = Column(Integer, primary_key=True, autoincrement=True)
    article_id            = Column(Integer, ForeignKey("articles.id"), unique=True, nullable=False)
    roberta_label         = Column(String)
    roberta_score         = Column(Float)
    vader_compound        = Column(Float)
    vader_positive        = Column(Float)
    vader_negative        = Column(Float)
    vader_neutral         = Column(Float)
    textblob_polarity     = Column(Float)
    textblob_subjectivity = Column(Float)
    scored_at             = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="sentiment_scores")


class EmotionScore(Base):
    __tablename__ = "emotion_scores"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    article_id       = Column(Integer, ForeignKey("articles.id"), unique=True, nullable=False)
    joy              = Column(Float, default=0)
    anger            = Column(Float, default=0)
    fear             = Column(Float, default=0)
    sadness          = Column(Float, default=0)
    disgust          = Column(Float, default=0)
    surprise         = Column(Float, default=0)
    neutral          = Column(Float, default=0)
    dominant_emotion = Column(String)
    scored_at        = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="emotion_scores")


class EntitySentiment(Base):
    __tablename__ = "entity_sentiments"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    article_id      = Column(Integer, ForeignKey("articles.id"), nullable=False)
    entity_text     = Column(String, nullable=False)
    entity_label    = Column(String)
    sentiment_label = Column(String)
    sentiment_score = Column(Float)
    context_snippet = Column(Text)
    scored_at       = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="entity_sentiments")


# ─────────────────────── HELPERS ────────────────────────

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)
    print("[DB] Tables created / verified.")


@contextmanager
def get_session():
    """Context manager for DB sessions with auto-commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_or_create_source(session, name, country=None, media_type="mainstream"):
    """Get existing source or create a new one."""
    source = session.query(Source).filter_by(name=name).first()
    if not source:
        source = Source(name=name, country=country, media_type=media_type)
        session.add(source)
        session.flush()  # get the id
    return source


def get_or_create_topic(session, name):
    """Get existing topic or create a new one."""
    topic = session.query(Topic).filter_by(name=name).first()
    if not topic:
        topic = Topic(name=name)
        session.add(topic)
        session.flush()
    return topic


def article_exists(session, url):
    """Check if an article URL is already in the database."""
    return session.query(Article).filter_by(url=url).first() is not None


def insert_article(session, source_name, title, description, full_text, url,
                   author=None, published_at=None, topics=None):
    """
    Insert a new article and link it to topics.
    Returns the Article object or None if it already exists.
    """
    if article_exists(session, url):
        return None

    source = get_or_create_source(session, source_name)
    word_count = len(full_text.split()) if full_text else 0

    article = Article(
        source_id=source.id,
        title=title,
        description=description,
        full_text=full_text,
        url=url,
        author=author,
        published_at=published_at,
        word_count=word_count,
    )
    session.add(article)
    session.flush()

    # Link topics
    if topics:
        for topic_name, relevance in topics:
            topic = get_or_create_topic(session, topic_name)
            link = ArticleTopic(
                article_id=article.id,
                topic_id=topic.id,
                relevance_score=relevance
            )
            session.add(link)

    return article


def insert_sentiment(session, article_id, roberta_label=None, roberta_score=None,
                     vader_compound=None, vader_pos=None, vader_neg=None, vader_neu=None,
                     tb_polarity=None, tb_subjectivity=None):
    """Insert sentiment scores for an article."""
    score = SentimentScore(
        article_id=article_id,
        roberta_label=roberta_label,
        roberta_score=roberta_score,
        vader_compound=vader_compound,
        vader_positive=vader_pos,
        vader_negative=vader_neg,
        vader_neutral=vader_neu,
        textblob_polarity=tb_polarity,
        textblob_subjectivity=tb_subjectivity,
    )
    session.add(score)
    return score


def insert_emotion(session, article_id, emotions: dict, dominant: str):
    """Insert emotion scores. emotions = {'joy': 0.1, 'anger': 0.8, ...}"""
    score = EmotionScore(
        article_id=article_id,
        joy=emotions.get("joy", 0),
        anger=emotions.get("anger", 0),
        fear=emotions.get("fear", 0),
        sadness=emotions.get("sadness", 0),
        disgust=emotions.get("disgust", 0),
        surprise=emotions.get("surprise", 0),
        neutral=emotions.get("neutral", 0),
        dominant_emotion=dominant,
    )
    session.add(score)
    return score


def insert_entity_sentiment(session, article_id, entity_text, entity_label,
                            sentiment_label, sentiment_score, context_snippet):
    """Insert entity-level sentiment."""
    ent = EntitySentiment(
        article_id=article_id,
        entity_text=entity_text,
        entity_label=entity_label,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
        context_snippet=context_snippet[:500] if context_snippet else None,
    )
    session.add(ent)
    return ent


def get_unscored_articles(session, limit=100):
    """Get articles that haven't been sentiment-scored yet."""
    scored_ids = session.query(SentimentScore.article_id)
    return (
        session.query(Article)
        .filter(~Article.id.in_(scored_ids))
        .filter(Article.full_text.isnot(None))
        .filter(Article.full_text != "")
        .limit(limit)
        .all()
    )


# ─────────────────── ANALYTICS QUERIES ──────────────────

def query_sentiment_by_source_and_topic(session, topic_name, days=30):
    """
    Core query: Average sentiment of a topic by publisher.
    Returns list of dicts with source_name, article_count, avg metrics.
    """
    sql = text("""
        SELECT
            s.name                          AS source_name,
            COUNT(*)                        AS article_count,
            ROUND(AVG(ss.vader_compound), 4)        AS avg_vader,
            ROUND(AVG(ss.roberta_score *
                CASE WHEN ss.roberta_label = 'negative' THEN -1
                     WHEN ss.roberta_label = 'neutral'  THEN 0
                     ELSE 1 END), 4)                AS avg_roberta,
            ROUND(AVG(ss.textblob_polarity), 4)     AS avg_polarity,
            ROUND(AVG(ss.textblob_subjectivity), 4) AS avg_subjectivity
        FROM articles a
        JOIN sources s              ON a.source_id = s.id
        JOIN article_topics at2     ON a.id = at2.article_id
        JOIN topics t               ON at2.topic_id = t.id
        JOIN sentiment_scores ss    ON a.id = ss.article_id
        WHERE t.name = :topic
          AND a.published_at >= date('now', :days_ago)
        GROUP BY s.name
        HAVING COUNT(*) >= :min_count
        ORDER BY avg_vader DESC
    """)
    rows = session.execute(sql, {
        "topic": topic_name,
        "days_ago": f"-{days} days",
        "min_count": 3,
    }).fetchall()
    return [dict(row._mapping) for row in rows]


def query_coverage_volume(session, days=30):
    """Coverage heatmap: how many articles each source wrote per topic."""
    sql = text("""
        SELECT
            s.name          AS source_name,
            t.name          AS topic_name,
            COUNT(*)        AS article_count
        FROM articles a
        JOIN sources s          ON a.source_id = s.id
        JOIN article_topics at2 ON a.id = at2.article_id
        JOIN topics t           ON at2.topic_id = t.id
        WHERE a.published_at >= date('now', :days_ago)
        GROUP BY s.name, t.name
        ORDER BY s.name, article_count DESC
    """)
    rows = session.execute(sql, {"days_ago": f"-{days} days"}).fetchall()
    return [dict(row._mapping) for row in rows]


def query_emotion_by_source(session, topic_name=None, days=30):
    """Average emotion distribution per source, optionally filtered by topic."""
    base = """
        SELECT
            s.name          AS source_name,
            COUNT(*)        AS article_count,
            ROUND(AVG(es.joy), 4)      AS avg_joy,
            ROUND(AVG(es.anger), 4)    AS avg_anger,
            ROUND(AVG(es.fear), 4)     AS avg_fear,
            ROUND(AVG(es.sadness), 4)  AS avg_sadness,
            ROUND(AVG(es.disgust), 4)  AS avg_disgust,
            ROUND(AVG(es.surprise), 4) AS avg_surprise
        FROM articles a
        JOIN sources s            ON a.source_id = s.id
        JOIN emotion_scores es    ON a.id = es.article_id
    """
    if topic_name:
        base += """
        JOIN article_topics at2   ON a.id = at2.article_id
        JOIN topics t             ON at2.topic_id = t.id
        WHERE t.name = :topic AND a.published_at >= date('now', :days_ago)
        """
    else:
        base += " WHERE a.published_at >= date('now', :days_ago) "

    base += " GROUP BY s.name HAVING COUNT(*) >= 3 ORDER BY s.name"

    params = {"days_ago": f"-{days} days"}
    if topic_name:
        params["topic"] = topic_name

    rows = session.execute(text(base), params).fetchall()
    return [dict(row._mapping) for row in rows]


def query_entity_sentiment_comparison(session, entity_text, days=30):
    """Compare how different sources cover a specific entity."""
    sql = text("""
        SELECT
            s.name              AS source_name,
            COUNT(*)            AS mention_count,
            ROUND(AVG(ens.sentiment_score *
                CASE WHEN ens.sentiment_label = 'negative' THEN -1
                     WHEN ens.sentiment_label = 'neutral'  THEN 0
                     ELSE 1 END), 4) AS avg_entity_sentiment
        FROM entity_sentiments ens
        JOIN articles a     ON ens.article_id = a.id
        JOIN sources s      ON a.source_id = s.id
        WHERE LOWER(ens.entity_text) = LOWER(:entity)
          AND a.published_at >= date('now', :days_ago)
        GROUP BY s.name
        HAVING COUNT(*) >= 2
        ORDER BY avg_entity_sentiment DESC
    """)
    rows = session.execute(sql, {
        "entity": entity_text,
        "days_ago": f"-{days} days",
    }).fetchall()
    return [dict(row._mapping) for row in rows]


def query_sentiment_trend(session, topic_name, source_name=None, days=60):
    """Weekly sentiment trend for a topic (optionally per source)."""
    sql = """
        SELECT
            strftime('%%Y-%%W', a.published_at) AS week,
            s.name                               AS source_name,
            COUNT(*)                             AS article_count,
            ROUND(AVG(ss.vader_compound), 4)     AS avg_vader
        FROM articles a
        JOIN sources s              ON a.source_id = s.id
        JOIN article_topics at2     ON a.id = at2.article_id
        JOIN topics t               ON at2.topic_id = t.id
        JOIN sentiment_scores ss    ON a.id = ss.article_id
        WHERE t.name = :topic
          AND a.published_at >= date('now', :days_ago)
    """
    params = {"topic": topic_name, "days_ago": f"-{days} days"}
    if source_name:
        sql += " AND s.name = :source "
        params["source"] = source_name

    sql += " GROUP BY week, s.name ORDER BY week"
    rows = session.execute(text(sql), params).fetchall()
    return [dict(row._mapping) for row in rows]


# ─────────────────────── INIT ───────────────────────────
if __name__ == "__main__":
    init_db()
    print("[DB] Database initialized successfully.")
