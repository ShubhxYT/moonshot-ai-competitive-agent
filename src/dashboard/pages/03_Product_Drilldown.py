import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import plotly.express as px
import streamlit as st
import pandas as pd

from src.dashboard.components import (
    load_products,
    load_reviews,
    load_sentiment,
    load_themes,
    no_data_message,
    get_brand_colors,
)

st.title("🔍 Product Drilldown")

products_df = load_products()
reviews_df = load_reviews()
sentiment_df = load_sentiment()
themes_dict = load_themes()

if products_df.empty:
    no_data_message()
    st.stop()

all_brands = sorted(products_df["brand"].unique())

st.sidebar.subheader("Select Product")

selected_brand = st.sidebar.selectbox("Brand", all_brands)

brand_products = products_df[products_df["brand"] == selected_brand]["title"].tolist()

if not brand_products:
    st.warning("No products found for this brand")
    st.stop()

product_options = {f"{i+1}. {p[:80]}{'...' if len(p) > 80 else ''}": i for i, p in enumerate(brand_products)} if len(brand_products) > 15 else {p: i for i, p in enumerate(brand_products)}

selected_product_title = st.sidebar.selectbox("Product", list(product_options.keys()))
selected_idx = product_options[selected_product_title]
product = products_df[products_df["brand"] == selected_brand].iloc[selected_idx]

asin = product["asin"]

st.markdown("### Product Details")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Price", f"₹{product['price']:,.0f}")
with col2:
    st.metric("MRP", f"₹{product.get('mrp', product['price']):,.0f}")
with col3:
    st.metric("Discount", f"{product.get('discount_pct', 0):.1f}%")
with col4:
    st.metric("Rating", f"{product.get('rating', 'N/A')} ⭐")

col5, col6, col7 = st.columns(3)
with col5:
    review_count = product.get("review_count", 0)
    review_count = int(review_count) if pd.notna(review_count) else 0
    st.metric("Reviews", f"{review_count:,}")
with col6:
    st.metric("Brand", product["brand"])
with col7:
    if product.get("url"):
        st.markdown(f"[View on Amazon]({product['url']})")

st.markdown(f"**{product['title']}**")

st.markdown("---")

product_sentiment = sentiment_df[sentiment_df["asin"] == asin] if not sentiment_df.empty else pd.DataFrame()

col_sent, col_aspects = st.columns(2)

with col_sent:
    st.subheader("Review Sentiment")
    if not product_sentiment.empty:
        avg_sent = product_sentiment["sentiment_score"].mean()
        sentiment_label = "Positive" if avg_sent > 0.2 else "Negative" if avg_sent < -0.2 else "Neutral"
        sentiment_color = "🟢" if avg_sent > 0.2 else "🔴" if avg_sent < -0.2 else "🟡"

        st.metric("Average Sentiment", f"{avg_sent:.2f}", delta=sentiment_label)
        st.metric("Total Reviews Analyzed", len(product_sentiment))

        fig_hist = px.histogram(
            product_sentiment,
            x="sentiment_score",
            nbins=20,
            title="Sentiment Distribution",
            labels={"sentiment_score": "Sentiment Score"},
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("No sentiment data for this product")

with col_aspects:
    st.subheader("Aspect-Level Sentiment")
    if not product_sentiment.empty:
        aspect_cols = [c for c in product_sentiment.columns if c.startswith("aspect_")]
        if aspect_cols:
            aspect_data = []
            for col in aspect_cols:
                counts = product_sentiment[col].value_counts()
                aspect_name = col.replace("aspect_", "")
                aspect_data.append({
                    "aspect": aspect_name,
                    "positive": counts.get("positive", 0),
                    "negative": counts.get("negative", 0),
                    "neutral": counts.get("neutral", 0),
                })
            aspect_df = pd.DataFrame(aspect_data)
            fig_aspects = px.bar(
                aspect_df,
                x="aspect",
                y=["positive", "negative", "neutral"],
                title="Aspect Sentiment Breakdown",
                barmode="stack",
                color_discrete_map={"positive": "#4ECDC4", "negative": "#FF6B6B", "neutral": "#CCCCCC"},
            )
            st.plotly_chart(fig_aspects, use_container_width=True)
        else:
            st.info("No aspect data available")
    else:
        st.info("No sentiment data for this product")

st.markdown("---")

st.subheader("Top Appreciation & Complaint Themes")

brand_themes = themes_dict.get(product["brand"], {})
col_pros, col_cons = st.columns(2)

with col_pros:
    st.markdown("🟢 **Top Appreciation**")
    pros = brand_themes.get("top_pros", [])[:5]
    for p in pros:
        theme = p.get("theme", str(p)) if isinstance(p, dict) else str(p)
        freq = p.get("frequency", "") if isinstance(p, dict) else ""
        st.markdown(f"- {theme}" + (f" ({freq})" if freq else ""))

with col_cons:
    st.markdown("🔴 **Top Complaints**")
    cons = brand_themes.get("top_cons", [])[:5]
    for c in cons:
        theme = c.get("theme", str(c)) if isinstance(c, dict) else str(c)
        freq = c.get("frequency", "") if isinstance(c, dict) else ""
        st.markdown(f"- {theme}" + (f" ({freq})" if freq else ""))

st.markdown("---")

st.subheader("Review Rating Timeline")

product_reviews = reviews_df[reviews_df["asin"] == asin] if not reviews_df.empty else pd.DataFrame()

if not product_reviews.empty and "date" in product_reviews.columns:
    product_reviews_copy = product_reviews.copy()
    product_reviews_copy["date"] = pd.to_datetime(product_reviews_copy["date"], errors="coerce")
    product_reviews_copy = product_reviews_copy.dropna(subset=["date"])
    if not product_reviews_copy.empty:
        timeline = product_reviews_copy.groupby(product_reviews_copy["date"].dt.to_period("M")).agg(
            avg_rating=("rating", "mean"),
            count=("review_id", "count"),
        ).reset_index()
        timeline["date"] = timeline["date"].astype(str)

        fig_timeline = px.line(
            timeline,
            x="date",
            y="avg_rating",
            markers=True,
            title="Average Rating Over Time",
            labels={"date": "Month", "avg_rating": "Average Rating"},
        )
        fig_timeline.update_yaxes(range=[0, 5.5])
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No date data available for timeline")
else:
    st.info("No review timeline data available")

if not product_reviews.empty:
    csv = product_reviews.to_csv(index=False)
    st.download_button("📥 Download Product Reviews as CSV", csv, f"reviews_{asin}.csv", "text/csv")
