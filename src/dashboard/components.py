import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@st.cache_data(ttl=300)
def load_products() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "cleaned" / "products.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=300)
def load_reviews() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "cleaned" / "reviews.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=300)
def load_brand_summary() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "cleaned" / "brand_summary.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=300)
def load_sentiment() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "outputs" / "sentiment_scores.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=300)
def load_themes() -> dict:
    path = PROJECT_ROOT / "data" / "outputs" / "themes.json"
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


@st.cache_data(ttl=300)
def load_competitive_matrix() -> pd.DataFrame:
    path = PROJECT_ROOT / "data" / "outputs" / "competitive_matrix.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=300)
def load_insights() -> dict:
    path = PROJECT_ROOT / "data" / "outputs" / "insights.json"
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def kpi_card(label: str, value: str, delta: str | None = None, help_text: str | None = None):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 10px;
                color: white;
                text-align: center;
                margin-bottom: 10px;
            ">
                <div style="font-size: 14px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
                <div style="font-size: 28px; font-weight: bold; margin-top: 5px;">{value}</div>
                {f'<div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">{delta}</div>' if delta else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )
    if help_text:
        st.caption(help_text)


def style_metric_card(label: str, value, prefix: str = "", suffix: str = ""):
    st.metric(label=label, value=f"{prefix}{value}{suffix}")


def get_brand_colors() -> dict:
    colors = {
        "Safari": "#FF6B6B",
        "Skybags": "#4ECDC4",
        "American Tourister": "#45B7D1",
        "VIP": "#96CEB4",
        "Aristocrat": "#FFEAA7",
        "Nasher Miles": "#DDA0DD",
    }
    products = load_products()
    for brand in products["brand"].unique():
        if brand not in colors:
            import hashlib
            hash_val = int(hashlib.md5(brand.encode()).hexdigest()[:6], 16)
            colors[brand] = f"#{hash_val:06x}"
    return colors


def no_data_message():
    st.warning("No data found. Please run the scraping and analysis pipeline first.")
    st.code("uv run python -m src.scraper.amazon_scraper\nuv run python -m src.scraper.review_scraper\nuv run python -m src.analysis.clean_data\nuv run python -m src.analysis.sentiment\nuv run python -m src.analysis.themes\nuv run python -m src.analysis.competitive")


def download_csv_button(df: pd.DataFrame, filename: str, button_label: str = "📥 Download CSV"):
    csv = df.to_csv(index=False)
    st.download_button(label=button_label, data=csv, file_name=filename, mime="text/csv")
