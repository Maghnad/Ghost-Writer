"""
Ghost Writer - Streamlit Dashboard
Interactive Bias Map and analytics dashboard for news sentiment analysis.

Run: streamlit run dashboard.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database.db_manager import (
    engine, get_session,
    query_sentiment_by_source_and_topic,
    query_coverage_volume,
    query_emotion_by_source,
    query_entity_sentiment_comparison,
    query_sentiment_trend,
)
from config import TOPIC_KEYWORDS, MIN_ARTICLES_FOR_STATS


# ─────────────────── PAGE CONFIG ────────────────────────
st.set_page_config(
    page_title="Ghost Writer — News Bias Analyzer",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────── CUSTOM CSS ─────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #E8E8E8;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #888;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    .metric-card {
        background: #1E1E2E;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────── SIDEBAR ────────────────────────────
st.sidebar.markdown("## 👻 Ghost Writer")
st.sidebar.markdown("**News Bias Analyzer**")
st.sidebar.markdown("---")

# Topic selector
available_topics = list(TOPIC_KEYWORDS.keys())
selected_topic = st.sidebar.selectbox(
    "📌 Select Topic",
    available_topics,
    index=0,
)

# Date range
days_range = st.sidebar.slider(
    "📅 Time Range (days)",
    min_value=7, max_value=180, value=30, step=7,
)

# Min article threshold
min_articles = st.sidebar.slider(
    "📊 Min Articles per Source",
    min_value=1, max_value=20, value=MIN_ARTICLES_FOR_STATS,
)

# Entity search
st.sidebar.markdown("---")
entity_search = st.sidebar.text_input(
    "🔍 Entity Search (e.g. Tesla, Biden)",
    value=selected_topic,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Built with ❤️ using Python, RoBERTa, VADER, SpaCy, and Streamlit"
)


# ─────────────────── HEADER ─────────────────────────────
st.markdown('<p class="main-header">👻 Ghost Writer</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Sentiment Analysis & Bias Detection for News Media</p>',
    unsafe_allow_html=True,
)


# ─────────────────── DATA LOADING ───────────────────────
@st.cache_data(ttl=300)  # cache for 5 minutes
def load_sentiment_data(topic, days):
    with get_session() as session:
        return query_sentiment_by_source_and_topic(session, topic, days)


@st.cache_data(ttl=300)
def load_coverage_data(days):
    with get_session() as session:
        return query_coverage_volume(session, days)


@st.cache_data(ttl=300)
def load_emotion_data(topic, days):
    with get_session() as session:
        return query_emotion_by_source(session, topic, days)


@st.cache_data(ttl=300)
def load_entity_data(entity, days):
    with get_session() as session:
        return query_entity_sentiment_comparison(session, entity, days)


@st.cache_data(ttl=300)
def load_trend_data(topic, days):
    with get_session() as session:
        return query_sentiment_trend(session, topic, days=days)


@st.cache_data(ttl=300)
def load_overview_stats():
    """Quick stats from the database."""
    try:
        df = pd.read_sql("SELECT COUNT(*) as cnt FROM articles", engine)
        total_articles = df["cnt"].iloc[0]

        df2 = pd.read_sql("SELECT COUNT(*) as cnt FROM sources", engine)
        total_sources = df2["cnt"].iloc[0]

        df3 = pd.read_sql("SELECT COUNT(*) as cnt FROM sentiment_scores", engine)
        scored = df3["cnt"].iloc[0]

        return total_articles, total_sources, scored
    except Exception:
        return 0, 0, 0


# ─────────────── OVERVIEW METRICS ───────────────────────
total_articles, total_sources, total_scored = load_overview_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Articles", f"{total_articles:,}")
col2.metric("News Sources", total_sources)
col3.metric("Analyzed", f"{total_scored:,}")
col4.metric("Selected Topic", selected_topic)

st.markdown("---")


# ─────────────── TAB LAYOUT ─────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Bias Map",
    "📈 Sentiment Trends",
    "🎭 Emotion Analysis",
    "🔥 Coverage Heatmap",
    "🔍 Entity Deep Dive",
])


# ═══════════════ TAB 1: BIAS MAP ════════════════════════
with tab1:
    st.subheader(f"Bias Map — \"{selected_topic}\" (Last {days_range} days)")
    st.caption(
        "Each dot is a publisher. X-axis = average sentiment (negative ← → positive). "
        "Y-axis = average subjectivity (factual ↓ → opinionated ↑)."
    )

    data = load_sentiment_data(selected_topic, days_range)

    if data:
        df = pd.DataFrame(data)

        fig = px.scatter(
            df,
            x="avg_vader",
            y="avg_subjectivity",
            size="article_count",
            text="source_name",
            color="avg_vader",
            color_continuous_scale="RdYlGn",
            range_color=[-1, 1],
            labels={
                "avg_vader": "Avg Sentiment (VADER)",
                "avg_subjectivity": "Avg Subjectivity",
                "article_count": "Article Count",
            },
            size_max=50,
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(
            height=550,
            template="plotly_dark",
            plot_bgcolor="#0E1117",
            paper_bgcolor="#0E1117",
            # Add quadrant lines
            shapes=[
                dict(type="line", x0=0, x1=0, y0=0, y1=1,
                     line=dict(color="gray", dash="dash", width=1)),
                dict(type="line", x0=-1, x1=1, y0=0.5, y1=0.5,
                     line=dict(color="gray", dash="dash", width=1)),
            ],
            annotations=[
                dict(x=-0.7, y=0.9, text="Negative & Opinionated",
                     showarrow=False, font=dict(color="#ff6b6b", size=11)),
                dict(x=0.7, y=0.9, text="Positive & Opinionated",
                     showarrow=False, font=dict(color="#51cf66", size=11)),
                dict(x=-0.7, y=0.1, text="Negative & Factual",
                     showarrow=False, font=dict(color="#ff922b", size=11)),
                dict(x=0.7, y=0.1, text="Positive & Factual",
                     showarrow=False, font=dict(color="#339af0", size=11)),
            ],
        )
        st.plotly_chart(fig, use_container_width=True)

        # Data table
        with st.expander("📊 View Raw Data"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info(
            f"No data found for **{selected_topic}** in the last {days_range} days. "
            "Run the pipeline first: `python scheduler.py --mode once`"
        )


# ═══════════════ TAB 2: SENTIMENT TRENDS ════════════════
with tab2:
    st.subheader(f"Sentiment Trends — \"{selected_topic}\"")

    trend_data = load_trend_data(selected_topic, days_range)

    if trend_data:
        df_trend = pd.DataFrame(trend_data)

        fig = px.line(
            df_trend,
            x="week",
            y="avg_vader",
            color="source_name",
            markers=True,
            labels={
                "week": "Week",
                "avg_vader": "Avg Sentiment (VADER)",
                "source_name": "Source",
            },
        )
        fig.update_layout(
            height=450,
            template="plotly_dark",
            plot_bgcolor="#0E1117",
            paper_bgcolor="#0E1117",
            hovermode="x unified",
            # Zero line
            shapes=[
                dict(type="line", x0=0, x1=1, xref="paper",
                     y0=0, y1=0, line=dict(color="gray", dash="dash", width=1)),
            ],
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trend data available yet.")


# ═══════════════ TAB 3: EMOTION ANALYSIS ════════════════
with tab3:
    st.subheader(f"Emotional Framing — \"{selected_topic}\"")
    st.caption("Radar chart showing the emotional fingerprint of each publisher's coverage.")

    emo_data = load_emotion_data(selected_topic, days_range)

    if emo_data:
        df_emo = pd.DataFrame(emo_data)
        emotions = ["avg_joy", "avg_anger", "avg_fear", "avg_sadness",
                     "avg_disgust", "avg_surprise"]
        emotion_labels = ["Joy", "Anger", "Fear", "Sadness", "Disgust", "Surprise"]

        fig = go.Figure()
        for _, row in df_emo.iterrows():
            values = [row[e] for e in emotions]
            values.append(values[0])  # close the polygon
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=emotion_labels + [emotion_labels[0]],
                name=row["source_name"],
                fill="toself",
                opacity=0.6,
            ))

        fig.update_layout(
            polar=dict(
                bgcolor="#0E1117",
                radialaxis=dict(visible=True, range=[0, 0.5]),
            ),
            template="plotly_dark",
            paper_bgcolor="#0E1117",
            height=500,
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Emotion breakdown table
        with st.expander("📊 View Emotion Breakdown"):
            display_df = df_emo[["source_name", "article_count"] + emotions].copy()
            display_df.columns = ["Source", "Articles"] + emotion_labels
            st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No emotion data available yet.")


# ═══════════════ TAB 4: COVERAGE HEATMAP ════════════════
with tab4:
    st.subheader(f"Coverage Volume Heatmap (Last {days_range} days)")
    st.caption(
        "How many articles each source published per topic. "
        "Empty cells = potential **omission bias**."
    )

    cov_data = load_coverage_data(days_range)

    if cov_data:
        df_cov = pd.DataFrame(cov_data)
        pivot = df_cov.pivot_table(
            index="source_name",
            columns="topic_name",
            values="article_count",
            aggfunc="sum",
            fill_value=0,
        )

        fig = px.imshow(
            pivot,
            labels=dict(x="Topic", y="Source", color="Articles"),
            color_continuous_scale="YlOrRd",
            aspect="auto",
            text_auto=True,
        )
        fig.update_layout(
            height=400,
            template="plotly_dark",
            paper_bgcolor="#0E1117",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No coverage data available yet.")


# ═══════════════ TAB 5: ENTITY DEEP DIVE ════════════════
with tab5:
    st.subheader(f"Entity Sentiment — \"{entity_search}\"")
    st.caption(
        "How different publishers talk about a specific entity "
        "(person, company, country)."
    )

    entity_data = load_entity_data(entity_search, days_range)

    if entity_data:
        df_ent = pd.DataFrame(entity_data)

        # Horizontal bar chart
        fig = px.bar(
            df_ent,
            x="avg_entity_sentiment",
            y="source_name",
            orientation="h",
            color="avg_entity_sentiment",
            color_continuous_scale="RdYlGn",
            range_color=[-1, 1],
            text="mention_count",
            labels={
                "avg_entity_sentiment": "Avg Entity Sentiment",
                "source_name": "Source",
                "mention_count": "Mentions",
            },
        )
        fig.update_traces(texttemplate="%{text} mentions", textposition="outside")
        fig.update_layout(
            height=400,
            template="plotly_dark",
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            yaxis=dict(autorange="reversed"),
            # Zero line
            shapes=[
                dict(type="line", x0=0, x1=0, y0=-0.5,
                     y1=len(df_ent) - 0.5,
                     line=dict(color="white", dash="dash", width=1)),
            ],
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📊 View Data"):
            st.dataframe(df_ent, use_container_width=True)
    else:
        st.info(
            f"No entity-level data found for **\"{entity_search}\"**. "
            "Try a different entity name."
        )


# ─────────────────── FOOTER ─────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.85rem;">
        Ghost Writer v1.0 — News Sentiment & Bias Detection<br>
        Pipeline: RSS Feeds → newspaper3k → RoBERTa + VADER + SpaCy → PostgreSQL → Streamlit<br>
        ⚠️ Sentiment ≠ Bias. These scores indicate tone, not journalistic quality.
    </div>
    """,
    unsafe_allow_html=True,
)
