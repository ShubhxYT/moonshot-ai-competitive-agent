import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from src.dashboard.components import (
    load_products,
    load_reviews,
    load_sentiment,
    load_brand_summary,
    no_data_message,
    get_brand_colors,
)

st.title("📊 Dashboard Overview")

products_df = load_products()
reviews_df = load_reviews()
sentiment_df = load_sentiment()
brand_summary_df = load_brand_summary()

if products_df.empty or reviews_df.empty:
    no_data_message()
    st.stop()

colors = get_brand_colors()
brand_list = sorted(products_df["brand"].unique())

st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Brands Tracked", len(brand_list))
with col2:
    st.metric("Products Analyzed", len(products_df))
with col3:
    st.metric("Reviews Analyzed", len(reviews_df))
with col4:
    avg_sentiment = sentiment_df["sentiment_score"].mean() if not sentiment_df.empty else 0
    st.metric("Avg Sentiment", f"{avg_sentiment:.2f}", delta=None)
with col5:
    avg_price = products_df["price"].mean()
    avg_discount = products_df["discount_pct"].mean()
    st.metric("Avg Discount", f"{avg_discount:.1f}%", delta=f"Avg price: ₹{avg_price:,.0f}")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Products per Brand")
    product_counts = products_df.groupby("brand").size().reset_index(name="count")
    product_counts = product_counts.sort_values("count", ascending=True)
    fig_products = px.bar(
        product_counts,
        x="count",
        y="brand",
        orientation="h",
        color="brand",
        color_discrete_map=colors,
    )
    fig_products.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_products, use_container_width=True)

with col_right:
    st.subheader("Reviews per Brand")
    review_counts = reviews_df.groupby("brand").size().reset_index(name="count")
    review_counts = review_counts.sort_values("count", ascending=True)
    fig_reviews = px.bar(
        review_counts,
        x="count",
        y="brand",
        orientation="h",
        color="brand",
        color_discrete_map=colors,
    )
    fig_reviews.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_reviews, use_container_width=True)

st.markdown("---")

col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("Sentiment Distribution")
    if not sentiment_df.empty:
        fig_sentiment = px.histogram(
            sentiment_df,
            x="sentiment_score",
            nbins=30,
            color="brand",
            color_discrete_map=colors,
            labels={"sentiment_score": "Sentiment Score"},
        )
        fig_sentiment.update_layout(height=350)
        st.plotly_chart(fig_sentiment, use_container_width=True)

with col_right2:
    st.subheader("Price vs Rating")
    fig_scatter = px.scatter(
        products_df,
        x="price",
        y="rating",
        color="brand",
        size="review_count",
        hover_name="title",
        color_discrete_map=colors,
        labels={"price": "Price (₹)", "rating": "Rating"},
    )
    fig_scatter.update_layout(height=350)
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

st.subheader("Pricing Overview")
if not brand_summary_df.empty and "avg_price" in brand_summary_df.columns:
    price_data = brand_summary_df.sort_values("avg_price")
    fig_pricing = go.Figure()
    fig_pricing.add_trace(go.Bar(
        name="Avg Price",
        x=price_data["brand_name"],
        y=price_data["avg_price"],
        marker_color="#667eea",
    ))
    fig_pricing.add_trace(go.Bar(
        name="Avg MRP",
        x=price_data["brand_name"],
        y=price_data["avg_mrp"],
        marker_color="#764ba2",
        opacity=0.4,
    ))
    fig_pricing.update_layout(barmode="group", height=400, title="Average Selling Price vs MRP")
    st.plotly_chart(fig_pricing, use_container_width=True)
