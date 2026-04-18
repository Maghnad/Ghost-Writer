"""
Ghost Writer - Emotion Analysis
Detects emotional framing in articles using DistilRoBERTa emotion classifier.
Emotions: joy, anger, fear, sadness, disgust, surprise, neutral
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from transformers import pipeline
from config import EMOTION_MODEL


# ─────────────── LAZY-LOADED SINGLETON ──────────────────
_emotion_pipeline = None


def _get_pipeline():
    global _emotion_pipeline
    if _emotion_pipeline is None:
        print("[NLP] Loading emotion classifier...")
        _emotion_pipeline = pipeline(
            "text-classification",
            model=EMOTION_MODEL,
            tokenizer=EMOTION_MODEL,
            max_length=512,
            truncation=True,
            top_k=None,  # return all emotion scores
        )
    return _emotion_pipeline


# ─────────────────── SCORING FUNCTIONS ──────────────────

def score_emotions(text: str) -> dict:
    """
    Classify emotions in text.
    Returns: {
        'scores': {'joy': 0.05, 'anger': 0.72, ...},
        'dominant': 'anger'
    }
    """
    if not text or not text.strip():
        return {
            "scores": {
                "joy": 0, "anger": 0, "fear": 0,
                "sadness": 0, "disgust": 0, "surprise": 0, "neutral": 1.0
            },
            "dominant": "neutral"
        }

    pipe = _get_pipeline()
    truncated = " ".join(text.split()[:500])
    results = pipe(truncated)[0]  # list of {'label': ..., 'score': ...}

    scores = {}
    for item in results:
        scores[item["label"].lower()] = round(item["score"], 4)

    dominant = max(scores, key=scores.get)

    return {
        "scores":   scores,
        "dominant":  dominant,
    }


def score_article_emotions(title: str, body: str) -> dict:
    """
    Score emotions on both headline and body, then combine.
    Headlines often carry stronger emotional framing.
    Returns combined scores with headline weight = 0.3, body weight = 0.7.
    """
    headline_result = score_emotions(title)
    body_result     = score_emotions(body)

    combined = {}
    all_labels = set(headline_result["scores"]) | set(body_result["scores"])

    for label in all_labels:
        h_score = headline_result["scores"].get(label, 0)
        b_score = body_result["scores"].get(label, 0)
        combined[label] = round(0.3 * h_score + 0.7 * b_score, 4)

    dominant = max(combined, key=combined.get)

    return {
        "scores":             combined,
        "dominant":           dominant,
        "headline_dominant":  headline_result["dominant"],
        "body_dominant":      body_result["dominant"],
    }


# ─────────────────────── CLI TEST ───────────────────────
if __name__ == "__main__":
    test_cases = [
        ("Tesla Shares Plummet Amid Safety Fears",
         "Investors are increasingly worried about Tesla's safety record."),
        ("Breakthrough: AI Cures New Disease!",
         "Scientists celebrate a joyful milestone in medical AI research."),
        ("Market Steady as Fed Holds Rates",
         "The Federal Reserve announced no change in interest rates today."),
    ]
    for title, body in test_cases:
        print(f"\nHeadline: {title}")
        result = score_article_emotions(title, body)
        print(f"  Dominant: {result['dominant']}")
        for emotion, score in sorted(result["scores"].items(), key=lambda x: -x[1]):
            bar = "█" * int(score * 30)
            print(f"    {emotion:10s} {score:.3f} {bar}")
