"""
Ghost Writer - Full-Text Extractor
Uses newspaper3k to extract full article text from URLs.
Falls back to the RSS description if extraction fails.
"""

import time
from typing import Optional
from newspaper import Article as NewsArticle, ArticleException


def extract_full_text(url: str, timeout: int = 10) -> Optional[str]:
    """
    Download and extract full article text from a URL.
    Returns the extracted text or None on failure.
    """
    try:
        article = NewsArticle(url)
        article.config.request_timeout = timeout
        article.config.browser_user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        article.download()
        article.parse()

        text = article.text.strip()
        if len(text) < 50:
            # Too short — likely a paywall or failed extraction
            return None

        return text

    except ArticleException as e:
        print(f"  [EXTRACT] ArticleException for {url[:60]}: {e}")
        return None
    except Exception as e:
        print(f"  [EXTRACT] Error for {url[:60]}: {type(e).__name__}: {e}")
        return None


def extract_batch(articles: list, delay: float = 1.0) -> list:
    """
    Extract full text for a batch of article dicts (from rss_fetcher).
    Adds 'full_text' key to each dict.
    Uses a polite delay between requests.
    """
    total = len(articles)
    success = 0

    for i, article in enumerate(articles):
        url = article.get("url", "")
        if not url:
            article["full_text"] = None
            continue

        print(f"  [EXTRACT] ({i+1}/{total}) {url[:70]}...")
        text = extract_full_text(url)

        if text:
            article["full_text"] = text
            success += 1
        else:
            # Fall back to RSS description
            article["full_text"] = article.get("description", "")

        # Polite delay to avoid rate limiting
        if i < total - 1:
            time.sleep(delay)

    print(f"  [EXTRACT] Completed: {success}/{total} full-text extractions")
    return articles


# ─────────────────────── CLI TEST ───────────────────────
if __name__ == "__main__":
    test_urls = [
        "https://www.reuters.com/technology/",
        "https://www.bbc.com/news/technology",
    ]
    for url in test_urls:
        print(f"\nExtracting: {url}")
        text = extract_full_text(url)
        if text:
            print(f"  Got {len(text)} chars | First 200: {text[:200]}...")
        else:
            print("  Extraction failed.")
