"""
Ghost Writer - RSS Feed Fetcher
Discovers articles from RSS feeds of major news outlets.
"""

import feedparser
from datetime import datetime
from time import mktime
from typing import List, Dict, Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED


def parse_published_date(entry) -> Optional[datetime]:
    """Extract and parse the published date from an RSS entry."""
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime.fromtimestamp(mktime(parsed))
            except (ValueError, OverflowError):
                continue
    return None


def fetch_feed(url: str, max_entries: int = MAX_ARTICLES_PER_FEED) -> List[Dict]:
    """
    Parse a single RSS feed URL and return structured article dicts.
    """
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[RSS] Error parsing {url}: {e}")
        return []

    articles = []
    for entry in feed.entries[:max_entries]:
        # Extract core fields with fallbacks
        title = getattr(entry, "title", "").strip()
        link  = getattr(entry, "link", "").strip()

        if not title or not link:
            continue

        # Description / summary
        description = getattr(entry, "summary", "")
        if not description:
            description = getattr(entry, "description", "")
        # Strip HTML tags from description
        import re
        description = re.sub(r"<[^>]+>", "", description).strip()

        author = getattr(entry, "author", None)
        published = parse_published_date(entry)

        articles.append({
            "title":        title,
            "description":  description[:1000],  # cap length
            "url":          link,
            "author":       author,
            "published_at": published,
        })

    return articles


def fetch_all_feeds() -> Dict[str, List[Dict]]:
    """
    Fetch articles from all configured RSS feeds.
    Returns: { source_name: [article_dict, ...] }
    """
    all_articles = {}
    total = 0

    for source_name, feed_urls in RSS_FEEDS.items():
        source_articles = []

        for url in feed_urls:
            entries = fetch_feed(url)
            source_articles.extend(entries)
            print(f"  [RSS] {source_name} | {url} → {len(entries)} entries")

        # Deduplicate by URL within same source
        seen_urls = set()
        unique = []
        for art in source_articles:
            if art["url"] not in seen_urls:
                seen_urls.add(art["url"])
                unique.append(art)

        all_articles[source_name] = unique
        total += len(unique)

    print(f"[RSS] Total unique articles fetched: {total}")
    return all_articles


# ─────────────────────── CLI TEST ───────────────────────
if __name__ == "__main__":
    print("Fetching all RSS feeds...\n")
    results = fetch_all_feeds()
    for source, articles in results.items():
        print(f"\n{'='*60}")
        print(f"  {source}: {len(articles)} articles")
        for a in articles[:3]:
            print(f"    - {a['title'][:80]}")
