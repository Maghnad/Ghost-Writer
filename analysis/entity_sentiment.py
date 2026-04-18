"""
Ghost Writer - Entity-Level Sentiment
Uses SpaCy NER to extract named entities and scores sentiment
in the surrounding context for each entity.
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import spacy
from typing import List, Dict
from config import SPACY_MODEL


# ─────────────── LAZY-LOADED MODELS ─────────────────────
_nlp = None

# Import sentiment scorer (reuse the RoBERTa pipeline)
from analysis.sentiment import score_roberta


def _get_nlp():
    global _nlp
    if _nlp is None:
        print(f"[NLP] Loading SpaCy model: {SPACY_MODEL}...")
        try:
            _nlp = spacy.load(SPACY_MODEL)
        except OSError:
            print(f"[NLP] Model not found. Installing {SPACY_MODEL}...")
            from spacy.cli import download
            download(SPACY_MODEL)
            _nlp = spacy.load(SPACY_MODEL)
    return _nlp


# ─────────── ENTITY TYPES WE CARE ABOUT ────────────────
RELEVANT_LABELS = {"ORG", "PERSON", "GPE", "PRODUCT", "EVENT", "NORP"}


def extract_entity_sentiments(text: str, min_context_len: int = 20) -> List[Dict]:
    """
    1. Run SpaCy NER to find named entities.
    2. For each entity, extract the surrounding sentence.
    3. Score sentiment on that sentence context.

    Returns list of dicts:
    [
        {
            'entity_text': 'Tesla',
            'entity_label': 'ORG',
            'sentiment_label': 'negative',
            'sentiment_score': 0.89,
            'context_snippet': 'Tesla faces regulatory...',
        },
        ...
    ]
    """
    if not text or not text.strip():
        return []

    nlp = _get_nlp()

    # Process text — limit to 100k chars for SpaCy memory safety
    doc = nlp(text[:100000])

    # Collect entities with their sentence context
    seen = set()  # avoid duplicate entity+sentence combos
    results = []

    for ent in doc.ents:
        if ent.label_ not in RELEVANT_LABELS:
            continue

        # Get the sentence containing this entity
        sent = ent.sent
        context = sent.text.strip()

        if len(context) < min_context_len:
            continue

        # Deduplicate: same entity text + same sentence
        dedup_key = (ent.text.lower(), context[:100])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Score sentiment on the context sentence
        sentiment = score_roberta(context)

        results.append({
            "entity_text":     ent.text,
            "entity_label":    ent.label_,
            "sentiment_label": sentiment["label"],
            "sentiment_score": sentiment["score"],
            "context_snippet": context[:500],
        })

    return results


def aggregate_entity_sentiments(entities: List[Dict]) -> Dict[str, Dict]:
    """
    Aggregate per-entity results across multiple mentions.
    Returns: {
        'Tesla': {
            'label': 'ORG',
            'mentions': 5,
            'avg_score': -0.42,
            'positive': 1,
            'negative': 3,
            'neutral': 1
        }
    }
    """
    from collections import defaultdict

    agg = defaultdict(lambda: {
        "label": None, "mentions": 0,
        "total_signed_score": 0.0,
        "positive": 0, "negative": 0, "neutral": 0
    })

    for ent in entities:
        key = ent["entity_text"]
        agg[key]["label"] = ent["entity_label"]
        agg[key]["mentions"] += 1
        agg[key][ent["sentiment_label"]] += 1

        # Compute signed score
        sign = {"positive": 1, "negative": -1, "neutral": 0}
        signed = sign.get(ent["sentiment_label"], 0) * ent["sentiment_score"]
        agg[key]["total_signed_score"] += signed

    # Compute averages
    result = {}
    for entity, data in agg.items():
        result[entity] = {
            "label":    data["label"],
            "mentions": data["mentions"],
            "avg_score": round(data["total_signed_score"] / data["mentions"], 4),
            "positive": data["positive"],
            "negative": data["negative"],
            "neutral":  data["neutral"],
        }

    return result


# ─────────────────────── CLI TEST ───────────────────────
if __name__ == "__main__":
    test_text = """
    Tesla announced record deliveries today, but CEO Elon Musk faced criticism
    from the SEC over his social media posts. Meanwhile, Ford reported strong
    EV sales growth. The White House praised both companies for advancing
    American manufacturing. Analysts at Goldman Sachs downgraded Tesla stock
    citing valuation concerns.
    """
    print("Extracting entity sentiments...\n")
    entities = extract_entity_sentiments(test_text)

    for e in entities:
        print(f"  [{e['entity_label']}] {e['entity_text']}: "
              f"{e['sentiment_label']} ({e['sentiment_score']:.3f})")
        print(f"    Context: {e['context_snippet'][:100]}...\n")

    print("\nAggregated:")
    agg = aggregate_entity_sentiments(entities)
    for entity, data in agg.items():
        print(f"  {entity}: avg={data['avg_score']:+.3f} "
              f"(+{data['positive']}/-{data['negative']}/~{data['neutral']})")
