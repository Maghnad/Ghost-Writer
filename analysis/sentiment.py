"""
Ghost Writer - Sentiment Analysis
Multi-model sentiment scoring using RoBERTa, VADER, and TextBlob.
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

from config import SENTIMENT_MODEL


# ─────────────── LAZY-LOADED SINGLETONS ─────────────────
_roberta_pipeline = None
_vader_analyzer   = None


def _get_roberta():
    global _roberta_pipeline
    if _roberta_pipeline is None:
        print("[NLP] Loading RoBERTa sentiment model...")
        _roberta_pipeline = pipeline(
            "sentiment-analysis",
            model=SENTIMENT_MODEL,
            tokenizer=SENTIMENT_MODEL,
            max_length=512,
            truncation=True,
        )
    return _roberta_pipeline


def _get_vader():
    global _vader_analyzer
    if _vader_analyzer is None:
        _vader_analyzer = SentimentIntensityAnalyzer()
    return _vader_analyzer


# ─────────────────── SCORING FUNCTIONS ──────────────────

def score_roberta(text: str) -> dict:
    """
    Score text with RoBERTa.
    Returns: {'label': 'positive'|'negative'|'neutral', 'score': float}
    """
    if not text or not text.strip():
        return {"label": "neutral", "score": 0.0}

    pipe = _get_roberta()
    # Truncate to ~500 words to stay within token limits
    truncated = " ".join(text.split()[:500])
    result = pipe(truncated)[0]

    return {
        "label": result["label"].lower(),
        "score": round(result["score"], 4),
    }


def score_vader(text: str) -> dict:
    """
    Score text with VADER.
    Returns: {'compound': float, 'pos': float, 'neg': float, 'neu': float}
    """
    if not text or not text.strip():
        return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}

    analyzer = _get_vader()
    scores = analyzer.polarity_scores(text)

    return {
        "compound": round(scores["compound"], 4),
        "pos":      round(scores["pos"], 4),
        "neg":      round(scores["neg"], 4),
        "neu":      round(scores["neu"], 4),
    }


def score_textblob(text: str) -> dict:
    """
    Score text with TextBlob.
    Returns: {'polarity': float (-1 to 1), 'subjectivity': float (0 to 1)}
    """
    if not text or not text.strip():
        return {"polarity": 0.0, "subjectivity": 0.0}

    blob = TextBlob(text)
    return {
        "polarity":     round(blob.sentiment.polarity, 4),
        "subjectivity": round(blob.sentiment.subjectivity, 4),
    }


def score_article(text: str) -> dict:
    """
    Run all three sentiment models on a piece of text.
    Returns combined dict of all scores.
    """
    roberta  = score_roberta(text)
    vader    = score_vader(text)
    textblob = score_textblob(text)

    return {
        "roberta_label":         roberta["label"],
        "roberta_score":         roberta["score"],
        "vader_compound":        vader["compound"],
        "vader_positive":        vader["pos"],
        "vader_negative":        vader["neg"],
        "vader_neutral":         vader["neu"],
        "textblob_polarity":     textblob["polarity"],
        "textblob_subjectivity": textblob["subjectivity"],
    }


# ─────────────────────── CLI TEST ───────────────────────
if __name__ == "__main__":
    test_texts = [
        "Tesla stock surged 15% today after record-breaking quarterly earnings.",
        "Tesla faces yet another setback as regulators announce a massive recall.",
        "Tesla delivered 420,000 vehicles in Q3, in line with analyst expectations.",
    ]
    for t in test_texts:
        print(f"\nText: {t[:80]}...")
        result = score_article(t)
        for k, v in result.items():
            print(f"  {k}: {v}")
