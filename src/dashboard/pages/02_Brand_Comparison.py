import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from src.dashboard.components import (
    load_products,
    load_reviews,
    load_sentiment,
    load_brand_summary,
    load_competitive_matrix,
    load_themes,
    no_data_message,
    get_brand_colors,
)

st.title("⚖️ Brand Comparison")

products_df = load_products()
reviews_df = load_reviews()
sentiment_df = load_sentiment()
themes = load_themes()
brand_summary_df = load_brand_summary()

if products_df.empty:
    no_data_message()
    st.stop()

colors = get_brand_colors()
all_brands = sorted(products_df["brand"].unique())

st.sidebar.subheader("Filters")
selected_brands = st.sidebar.multiselect("Select Brands", all_brands, default=all_brands)
min_rating = st.sidebar.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.5)
price_range = st.sidebar.slider(
    "Price Range (₹)",
    int(products_df["price"].min()),
    int(products_df["price"].max()),
    (int(products_df["price"].min()), int(products_df["price"].max())),
)

filtered_products = products_df[
    (products_df["brand"].isin(selected_brands))
    & (products_df["rating"] >= min_rating)
    & (products_df["price"].between(price_range[0], price_range[1]))
]

filtered_sentiment = sentiment_df[sentiment_df["brand"].isin(selected_brands)] if not sentiment_df.empty else sentiment_df

st.subheader("Side-by-Side Comparison")

if not brand_summary_df.empty:
    comparison_df = brand_summary_df[brand_summary_df["brand_name"].isin(selected_brands)].copy()
    display_cols = [c for c in ["brand_name", "product_count", "avg_price", "avg_discount", "avg_rating", "total_reviews"] if c in comparison_df.columns]
    if "avg_sentiment" in comparison_df.columns:
        display_cols.append("avg_sentiment")
    st.dataframe(
        comparison_df[display_cols].sort_values("brand_name"),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

col_radar, col_bands = st.columns(2)

with col_radar:
    st.subheader("Brand Radar Chart")
    if not brand_summary_df.empty and len(selected_brands) >= 2:
        radar_data = brand_summary_df[brand_summary_df["brand_name"].isin(selected_brands)].copy()

        radar_categories = []
        for col in ["avg_rating", "avg_discount", "avg_sentiment", "total_reviews"]:
            if col in radar_data.columns:
                radar_categories.append(col)

        if radar_categories:
            radar_df = radar_data[["brand_name"] + radar_categories].copy()
            for col in radar_categories:
                min_val = radar_df[col].min()
                max_val = radar_df[col].max()
                if max_val > min_val:
                    radar_df[col] = ((radar_df[col] - min_val) / (max_val - min_val)) * 100
                else:
                    radar_df[col] = 50

            fig_radar = go.Figure()
            for _, row in radar_df.iterrows():
                fig_radar.add_trace(go.Scatterpolar(
                    r=[row[c] for c in radar_categories] + [row[radar_categories[0]]],
                    theta=radar_categories + [radar_categories[0]],
                    fill="toself",
                    name=row["brand_name"],
                ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=400)
            st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Select at least 2 brands for radar chart")

with col_bands:
    st.subheader("Price Band Distribution")
    if "price_band" not in filtered_products.columns:
        def compute_price_bands(price):
            if price <= 2000: return "Value"
            elif price <= 5000: return "Mid-Range"
            elif price <= 10000: return "Premium"
            else: return "Luxury"
        filtered_products = filtered_products.copy()
        filtered_products["price_band"] = filtered_products["price"].apply(compute_price_bands)

    band_counts = filtered_products.groupby(["brand", "price_band"]).size().reset_index(name="count")
    band_order = ["Value", "Mid-Range", "Premium", "Luxury"]
    band_counts["price_band"] = pd.Categorical(band_counts["price_band"], categories=band_order, ordered=True)

    fig_bands = px.bar(
        band_counts,
        x="brand",
        y="count",
        color="price_band",
        title="Products by Price Band",
        color_discrete_map={"Value": "#4ECDC4", "Mid-Range": "#667eea", "Premium": "#764ba2", "Luxury": "#FF6B6B"},
    )
    fig_bands.update_layout(height=400)
    st.plotly_chart(fig_bands, use_container_width=True)

st.markdown("---")

st.subheader("Top Pros & Cons by Brand")

pros_cons_cols = st.columns(len(selected_brands))
for i, brand in enumerate(selected_brands):
    with pros_cons_cols[i]:
        st.markdown(f"**{brand}**")
        brand_themes = themes.get(brand, {})
        if brand_themes:
            pros = brand_themes.get("top_pros", [])[:3]
            cons = brand_themes.get("top_cons", [])[:3]
            if pros:
                st.markdown("🟢 **Pros:**")
                for p in pros:
                    st.markdown(f"- {p.get('theme', str(p))}")
            if cons:
                st.markdown("🔴 **Cons:**")
                for c in cons:
                    st.markdown(f"- {c.get('theme', str(c))}")
        else:
            st.info("No theme data")

st.markdown("---")

if st.button("📥 Download Filtered Data as CSV"):
    csv = filtered_products.to_csv(index=False)
    st.download_button("Download", csv, "brand_comparison.csv", "text/csv")
