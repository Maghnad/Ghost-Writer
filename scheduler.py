"""
Ghost Writer - Pipeline Scheduler
Orchestrates the full pipeline: fetch → extract → tag → analyze → store.
Can run as a one-shot or on a schedule via APScheduler.
"""

import os, sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from config import FETCH_INTERVAL_HOURS
from database.db_manager import (
    init_db, get_session, insert_article,
    insert_sentiment, insert_emotion, insert_entity_sentiment,
    get_unscored_articles
)
from ingestion.rss_fetcher import fetch_all_feeds
from ingestion.text_extractor import extract_batch
from analysis.topic_tagger import tag_article
from analysis.sentiment import score_article
from analysis.emotion import score_article_emotions
from analysis.entity_sentiment import extract_entity_sentiments


def run_ingestion_pipeline():
    """
    Phase 1: Fetch RSS → Extract full text → Tag topics → Store in DB.
    """
    print(f"\n{'='*70}")
    print(f"  [PIPELINE] Ingestion started at {datetime.now().isoformat()}")
    print(f"{'='*70}\n")

    # Step 1: Fetch RSS feeds
    print("[STEP 1] Fetching RSS feeds...")
    all_feeds = fetch_all_feeds()

    total_new = 0

    for source_name, articles in all_feeds.items():
        print(f"\n[STEP 2] Extracting full text for {source_name} "
              f"({len(articles)} articles)...")
        articles = extract_batch(articles, delay=0.5)

        # Step 3: Tag topics and store
        print(f"[STEP 3] Tagging topics and storing {source_name}...")
        with get_session() as session:
            for art in articles:
                # Tag topics
                topics = tag_article(
                    art.get("title", ""),
                    art.get("description", ""),
                    art.get("full_text", ""),
                )

                # Insert article
                db_article = insert_article(
                    session,
                    source_name=source_name,
                    title=art.get("title", ""),
                    description=art.get("description", ""),
                    full_text=art.get("full_text", ""),
                    url=art.get("url", ""),
                    author=art.get("author"),
                    published_at=art.get("published_at"),
                    topics=topics if topics else None,
                )

                if db_article:
                    total_new += 1

    print(f"\n[INGESTION DONE] {total_new} new articles stored.\n")
    return total_new


def run_analysis_pipeline(batch_size: int = 50):
    """
    Phase 2: Score unscored articles with sentiment, emotion, and entity analysis.
    """
    print(f"\n{'='*70}")
    print(f"  [PIPELINE] Analysis started at {datetime.now().isoformat()}")
    print(f"{'='*70}\n")

    with get_session() as session:
        unscored = get_unscored_articles(session, limit=batch_size)
        print(f"[ANALYSIS] Found {len(unscored)} unscored articles.\n")

        for i, article in enumerate(unscored):
            text = article.full_text or article.description or article.title
            title = article.title or ""

            print(f"  [{i+1}/{len(unscored)}] Scoring: {title[:70]}...")

            try:
                # ---- Sentiment (RoBERTa + VADER + TextBlob) ----
                sent = score_article(text)
                insert_sentiment(
                    session,
                    article_id=article.id,
                    roberta_label=sent["roberta_label"],
                    roberta_score=sent["roberta_score"],
                    vader_compound=sent["vader_compound"],
                    vader_pos=sent["vader_positive"],
                    vader_neg=sent["vader_negative"],
                    vader_neu=sent["vader_neutral"],
                    tb_polarity=sent["textblob_polarity"],
                    tb_subjectivity=sent["textblob_subjectivity"],
                )

                # ---- Emotion ----
                emo = score_article_emotions(title, text)
                insert_emotion(
                    session,
                    article_id=article.id,
                    emotions=emo["scores"],
                    dominant=emo["dominant"],
                )

                # ---- Entity-Level Sentiment ----
                entities = extract_entity_sentiments(text)
                for ent in entities:
                    insert_entity_sentiment(
                        session,
                        article_id=article.id,
                        entity_text=ent["entity_text"],
                        entity_label=ent["entity_label"],
                        sentiment_label=ent["sentiment_label"],
                        sentiment_score=ent["sentiment_score"],
                        context_snippet=ent["context_snippet"],
                    )

                print(f"    ✓ Sentiment: {sent['roberta_label']} | "
                      f"Emotion: {emo['dominant']} | "
                      f"Entities: {len(entities)}")

            except Exception as e:
                print(f"    ✗ Error: {type(e).__name__}: {e}")
                continue

    print(f"\n[ANALYSIS DONE] Scored {len(unscored)} articles.\n")


def run_full_pipeline():
    """Run both ingestion and analysis."""
    run_ingestion_pipeline()
    run_analysis_pipeline()


def start_scheduler():
    """
    Start APScheduler to run the pipeline at regular intervals.
    Also runs once immediately on startup.
    """
    from apscheduler.schedulers.blocking import BlockingScheduler

    print(f"[SCHEDULER] Starting Ghost Writer pipeline scheduler...")
    print(f"[SCHEDULER] Interval: every {FETCH_INTERVAL_HOURS} hours\n")

    # Run once immediately
    run_full_pipeline()

    # Schedule recurring runs
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_full_pipeline,
        "interval",
        hours=FETCH_INTERVAL_HOURS,
        id="ghost_writer_pipeline",
        name="Ghost Writer Full Pipeline",
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[SCHEDULER] Shutting down...")
        scheduler.shutdown()


# ─────────────────────── CLI ────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ghost Writer Pipeline")
    parser.add_argument(
        "--mode",
        choices=["once", "schedule", "ingest", "analyze", "init-db"],
        default="once",
        help="Run mode: 'once' (full pipeline once), 'schedule' (recurring), "
             "'ingest' (fetch only), 'analyze' (score only), 'init-db' (create tables)"
    )
    args = parser.parse_args()

    if args.mode == "init-db":
        init_db()
    elif args.mode == "ingest":
        init_db()
        run_ingestion_pipeline()
    elif args.mode == "analyze":
        run_analysis_pipeline()
    elif args.mode == "schedule":
        init_db()
        start_scheduler()
    else:  # "once"
        init_db()
        run_full_pipeline()
