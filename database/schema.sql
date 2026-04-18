-- Ghost Writer - Database Schema
-- Compatible with both PostgreSQL and SQLite

-- ─────────────────────── SOURCES ───────────────────────
CREATE TABLE IF NOT EXISTS sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    country         TEXT,
    media_type      TEXT DEFAULT 'mainstream',   -- mainstream, tabloid, wire, state
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────── ARTICLES ──────────────────────
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER NOT NULL REFERENCES sources(id),
    title           TEXT NOT NULL,
    description     TEXT,
    full_text       TEXT,
    url             TEXT UNIQUE NOT NULL,
    author          TEXT,
    published_at    TIMESTAMP,
    fetched_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    word_count      INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_articles_source      ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_published    ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_url          ON articles(url);

-- ─────────────────────── TOPICS ────────────────────────
CREATE TABLE IF NOT EXISTS topics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE
);

-- ─────────────── ARTICLE ↔ TOPIC (M2M) ────────────────
CREATE TABLE IF NOT EXISTS article_topics (
    article_id      INTEGER NOT NULL REFERENCES articles(id),
    topic_id        INTEGER NOT NULL REFERENCES topics(id),
    relevance_score REAL DEFAULT 1.0,   -- how strongly the article matches
    PRIMARY KEY (article_id, topic_id)
);

CREATE INDEX IF NOT EXISTS idx_at_topic ON article_topics(topic_id);

-- ─────────────────── SENTIMENT SCORES ──────────────────
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id              INTEGER UNIQUE NOT NULL REFERENCES articles(id),
    -- RoBERTa sentiment
    roberta_label           TEXT,       -- positive / negative / neutral
    roberta_score           REAL,       -- confidence 0-1
    -- VADER
    vader_compound          REAL,       -- -1 to 1
    vader_positive          REAL,
    vader_negative          REAL,
    vader_neutral           REAL,
    -- TextBlob
    textblob_polarity       REAL,       -- -1 to 1
    textblob_subjectivity   REAL,       -- 0 (objective) to 1 (subjective)
    scored_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ss_article ON sentiment_scores(article_id);

-- ─────────────────── EMOTION SCORES ────────────────────
CREATE TABLE IF NOT EXISTS emotion_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id      INTEGER UNIQUE NOT NULL REFERENCES articles(id),
    joy             REAL DEFAULT 0,
    anger           REAL DEFAULT 0,
    fear            REAL DEFAULT 0,
    sadness         REAL DEFAULT 0,
    disgust         REAL DEFAULT 0,
    surprise        REAL DEFAULT 0,
    neutral         REAL DEFAULT 0,
    dominant_emotion TEXT,
    scored_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_es_article ON emotion_scores(article_id);

-- ─────────────── ENTITY-LEVEL SENTIMENT ────────────────
CREATE TABLE IF NOT EXISTS entity_sentiments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id      INTEGER NOT NULL REFERENCES articles(id),
    entity_text     TEXT NOT NULL,        -- "Tesla", "Elon Musk", etc.
    entity_label    TEXT,                 -- SpaCy label: ORG, PERSON, GPE...
    sentiment_label TEXT,                 -- positive / negative / neutral
    sentiment_score REAL,                 -- confidence
    context_snippet TEXT,                 -- surrounding sentence
    scored_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ent_article  ON entity_sentiments(article_id);
CREATE INDEX IF NOT EXISTS idx_ent_entity   ON entity_sentiments(entity_text);

-- ──────────────── USEFUL AGGREGATE VIEW ────────────────
CREATE VIEW IF NOT EXISTS v_article_analysis AS
SELECT
    a.id            AS article_id,
    s.name          AS source_name,
    a.title,
    a.published_at,
    a.word_count,
    ss.roberta_label,
    ss.roberta_score,
    ss.vader_compound,
    ss.textblob_polarity,
    ss.textblob_subjectivity,
    es.dominant_emotion,
    es.joy, es.anger, es.fear, es.sadness
FROM articles a
JOIN sources s             ON a.source_id = s.id
LEFT JOIN sentiment_scores ss ON a.id = ss.article_id
LEFT JOIN emotion_scores es   ON a.id = es.article_id;
