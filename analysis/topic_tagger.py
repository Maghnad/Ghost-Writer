"""
Ghost Writer - Topic Tagger
Assigns topic tags to articles based on keyword matching.
Uses the TOPIC_KEYWORDS config for mapping.
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import List, Tuple
from config import TOPIC_KEYWORDS


def tag_article(title: str, description: str = "", full_text: str = "") -> List[Tuple[str, float]]:
    """
    Assign topic tags to an article based on keyword matching.

    Scoring:
    - Title match:       weight 3x (headlines are most indicative)
    - Description match: weight 2x
    - Body match:        weight 1x per occurrence (capped at 5)

    Returns: list of (topic_name, relevance_score) tuples, sorted by score.
    Only topics with score > 0 are returned.
    """
    title_lower = (title or "").lower()
    desc_lower  = (description or "").lower()
    body_lower  = (full_text or "").lower()

    matches = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = 0.0

        for kw in keywords:
            kw_lower = kw.lower()

            # Title match — strongest signal
            if kw_lower in title_lower:
                score += 3.0

            # Description match
            if kw_lower in desc_lower:
                score += 2.0

            # Body matches — count occurrences, cap at 5
            if body_lower:
                count = body_lower.count(kw_lower)
                score += min(count, 5) * 1.0

        if score > 0:
            matches.append((topic, round(score, 2)))

    # Sort by relevance score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


# ─────────────────────── CLI TEST ───────────────────────
if __name__ == "__main__":
    test_cases = [
        {
            "title": "Tesla Recalls 500,000 Vehicles Over Safety Defect",
            "description": "Elon Musk's EV company faces pressure from regulators.",
            "full_text": "Tesla Inc. announced a recall of 500,000 vehicles. The stock market reacted negatively."
        },
        {
            "title": "OpenAI Launches GPT-5 With Breakthrough Reasoning",
            "description": "The new AI model shows significant improvements in machine learning benchmarks.",
            "full_text": "OpenAI released its latest large language model today. Deep learning researchers praised the results."
        },
        {
            "title": "Congress Debates New Climate Bill",
            "description": "Republican and Democrat senators clash over carbon emissions targets.",
            "full_text": "The Senate held hearings on the proposed net zero legislation. Fossil fuel lobbyists opposed the bill."
        },
    ]

    for case in test_cases:
        topics = tag_article(case["title"], case["description"], case["full_text"])
        print(f"\n  Title: {case['title']}")
        for topic, score in topics:
            print(f"    [{score:5.1f}] {topic}")
