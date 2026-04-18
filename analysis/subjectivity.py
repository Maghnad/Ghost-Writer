"""
Ghost Writer - Subjectivity Analysis
Measures how opinionated vs. factual an article is using TextBlob.
Also provides a headline-vs-body subjectivity comparison to detect clickbait framing.
"""

from textblob import TextBlob


def score_subjectivity(text: str) -> float:
    """
    Score subjectivity of text.
    Returns float: 0.0 (fully objective) to 1.0 (fully subjective).
    """
    if not text or not text.strip():
        return 0.0
    return round(TextBlob(text).sentiment.subjectivity, 4)


def analyze_framing(title: str, body: str) -> dict:
    """
    Compare headline subjectivity vs. body subjectivity.
    A large gap suggests clickbait or editorial framing in headlines.

    Returns: {
        'headline_subjectivity': float,
        'body_subjectivity': float,
        'gap': float,              # headline - body
        'clickbait_flag': bool,    # True if gap > 0.3
    }
    """
    h_sub = score_subjectivity(title)
    b_sub = score_subjectivity(body)
    gap = round(h_sub - b_sub, 4)

    return {
        "headline_subjectivity": h_sub,
        "body_subjectivity":     b_sub,
        "gap":                   gap,
        "clickbait_flag":        gap > 0.3,
    }


# ─────────────────────── CLI TEST ───────────────────────
if __name__ == "__main__":
    cases = [
        ("SHOCKING: Tesla's Terrible Secret Exposed!",
         "Tesla Inc. reported quarterly revenue of $25.2 billion, a 9% increase year-over-year."),
        ("Fed Holds Interest Rates Steady",
         "The Federal Reserve announced today that it would maintain the federal funds rate."),
        ("This Incredible AI Will Change Everything Forever!",
         "A new machine learning model achieved 92% accuracy on the benchmark dataset."),
    ]
    for title, body in cases:
        result = analyze_framing(title, body)
        flag = " ⚠ CLICKBAIT" if result["clickbait_flag"] else ""
        print(f"\n  Headline: {title}")
        print(f"  H-Subj: {result['headline_subjectivity']:.3f} | "
              f"B-Subj: {result['body_subjectivity']:.3f} | "
              f"Gap: {result['gap']:+.3f}{flag}")
