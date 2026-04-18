# 👻 Ghost Writer — News Sentiment & Bias Detection

A full-stack Python pipeline that collects news articles from major outlets, runs multi-model NLP analysis, and visualizes media bias through an interactive Streamlit dashboard.

## What It Does

Ghost Writer answers questions like:
- *"Does CNBC cover Tesla more positively than Reuters?"*
- *"Which outlets use the most emotional language about climate change?"*
- *"Who isn't covering this story at all?"*

It does this by combining **5 distinct bias signals**:
1. **Sentiment** — RoBERTa transformer + VADER lexicon scoring
2. **Subjectivity** — TextBlob objectivity vs. opinion measurement
3. **Emotion Framing** — Joy, anger, fear, sadness detection via DistilRoBERTa
4. **Entity-Level Sentiment** — SpaCy NER + per-entity tone analysis
5. **Coverage Volume** — Omission bias detection via article counts

## Architecture

```
[Cron / APScheduler]
        │
        ▼
[RSS Feeds] ──fetch──▶ [feedparser + newspaper3k]
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            [NLP Analysis]        [PostgreSQL/SQLite]
            • RoBERTa Sentiment   • articles
            • VADER               • sentiment_scores
            • Emotion Classifier  • emotion_scores
            • SpaCy NER           • entity_sentiments
            • TextBlob            • article_topics
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    [Streamlit Dashboard]
                    • Bias Map (scatter)
                    • Sentiment Trends (line)
                    • Emotion Radar (polar)
                    • Coverage Heatmap
                    • Entity Deep Dive (bar)
```

## Quick Start

### 1. Install Dependencies

```bash
# Clone and enter project
cd ghost-writer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install packages
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm
python -m textblob.download_corpora
```

### 2. Configure

Edit `config.py` to:
- Add/remove RSS feed sources
- Adjust topic keywords
- Switch between SQLite (default) and PostgreSQL
- Set fetch interval

For PostgreSQL, set the environment variable:
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/ghost_writer"
```

### 3. Initialize Database

```bash
python scheduler.py --mode init-db
```

### 4. Run the Pipeline

```bash
# One-shot: fetch + analyze
python scheduler.py --mode once

# Or run steps separately:
python scheduler.py --mode ingest    # fetch articles only
python scheduler.py --mode analyze   # score unscored articles only

# Recurring schedule (every 6 hours by default):
python scheduler.py --mode schedule
```

### 5. Launch Dashboard

```bash
streamlit run dashboard.py
```

Open `http://localhost:8501` in your browser.

## Project Structure

```
ghost-writer/
├── config.py                  # Central configuration
├── scheduler.py               # Pipeline orchestrator + CLI
├── dashboard.py               # Streamlit visualization app
├── requirements.txt
├── README.md
│
├── ingestion/
│   ├── rss_fetcher.py         # RSS feed discovery
│   └── text_extractor.py      # Full-text extraction (newspaper3k)
│
├── analysis/
│   ├── sentiment.py           # RoBERTa + VADER + TextBlob
│   ├── emotion.py             # Emotion classification
│   ├── entity_sentiment.py    # SpaCy NER + per-entity scoring
│   ├── subjectivity.py        # Subjectivity & clickbait detection
│   └── topic_tagger.py        # Keyword-based topic assignment
│
└── database/
    ├── schema.sql             # SQL table definitions
    └── db_manager.py          # SQLAlchemy ORM + query functions
```

## Key SQL Queries

The project includes pre-built analytics queries in `db_manager.py`:

- **Sentiment by source & topic** — "Average Tesla sentiment: CNBC vs Reuters"
- **Coverage volume** — Topic × Source article count matrix
- **Emotion distribution** — Average emotion per publisher
- **Entity comparison** — How sources cover specific people/companies
- **Sentiment trends** — Weekly rolling averages over time

## Dashboard Tabs

| Tab | Visualization | Bias Signal |
|-----|--------------|-------------|
| 🗺️ Bias Map | Scatter plot (sentiment vs. subjectivity) | Tone + opinion level |
| 📈 Trends | Line chart (weekly sentiment) | Sentiment drift |
| 🎭 Emotions | Radar chart (emotion fingerprint) | Emotional framing |
| 🔥 Coverage | Heatmap (article counts) | Omission bias |
| 🔍 Entity | Horizontal bar chart | Per-entity tone |

## Limitations & Caveats

- **Sentiment ≠ Bias.** Negative sentiment about a stock crash is factual reporting, not bias.
- **Lexicon + transformer models can't detect** sarcasm, omission by framing, or visual bias.
- **RSS feeds don't guarantee full text** — some sites block scraping. The pipeline falls back to headlines/descriptions.
- **Keyword-based topic tagging** is approximate. An article mentioning "Apple" the fruit will be tagged as Tech Giants.
- For production use, consider fine-tuning on a media bias dataset (MBFC, AllSides) for higher accuracy.

## Extending the Project

- **Add more sources:** Edit `RSS_FEEDS` in `config.py`
- **Add topics:** Edit `TOPIC_KEYWORDS` in `config.py`
- **Upgrade NER:** Switch `SPACY_MODEL` to `en_core_web_trf` for better accuracy
- **Use GPU:** Install `torch` with CUDA support for faster transformer inference
- **Switch to PostgreSQL:** Set `DATABASE_URL` env var for production scale

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Ingestion | feedparser, newspaper3k |
| Sentiment | RoBERTa (HuggingFace), VADER, TextBlob |
| Emotion | DistilRoBERTa (j-hartmann) |
| NER | SpaCy |
| Database | SQLAlchemy + PostgreSQL/SQLite |
| Dashboard | Streamlit + Plotly |
| Scheduler | APScheduler |

---

*Built as a data engineering + NLP portfolio project.*
