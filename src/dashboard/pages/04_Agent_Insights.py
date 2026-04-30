import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import plotly.express as px
import streamlit as st
import pandas as pd

from src.dashboard.components import (
    load_products,
    load_competitive_matrix,
    load_insights,
    no_data_message,
)

st.title("🤖 Agent Insights")

products_df = load_products()
insights_data = load_insights()

if products_df.empty:
    no_data_message()
    st.stop()

st.markdown("### AI-Generated Competitive Intelligence Insights")
st.markdown("---")

if st.button("🔄 Regenerate Insights", type="primary"):
    from src.analysis.insights_generator import InsightsGenerator
    with st.spinner("Generating insights with Llama 70B..."):
        try:
            generator = InsightsGenerator()
            insights_list = generator.generate_insights()
            insights_data = load_insights()
            st.success("Insights regenerated!")
        except Exception as e:
            st.error(f"Failed to generate insights: {e}")
            st.stop()

agent_insights = insights_data.get("agent_insights", [])

if not agent_insights:
    st.info("No insights generated yet. Click 'Regenerate Insights' to generate.")
    st.stop()

category_icons = {
    "pricing": "💰",
    "quality": "⭐",
    "positioning": "🎯",
    "opportunity": "🚀",
    "risk": "⚠️",
}
category_colors = {
    "pricing": "#667eea",
    "quality": "#4ECDC4",
    "positioning": "#45B7D1",
    "opportunity": "#96CEB4",
    "risk": "#FF6B6B",
}

for i, insight in enumerate(agent_insights[:5]):
    if isinstance(insight, str):
        insight = {"insight": insight, "evidence": "", "implication": "", "category": "opportunity"}

    category = insight.get("category", "opportunity")
    icon = category_icons.get(category, "💡")
    color = category_colors.get(category, "#764ba2")

    with st.container():
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, {color}22 0%, {color}11 100%);
                border-left: 4px solid {color};
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 15px;
            ">
                <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">
                    {icon} Insight #{i+1}: {insight.get('category', '').title()}
                </div>
                <div style="font-size: 16px; margin-bottom: 10px;">
                    {insight.get('insight', '')}
                </div>
                <div style="font-size: 13px; color: #666; margin-bottom: 5px;">
                    📊 <strong>Evidence:</strong> {insight.get('evidence', '')}
                </div>
                <div style="font-size: 13px; color: #444;">
                    💡 <strong>Implication:</strong> {insight.get('implication', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

st.subheader("Anomalies Detected")

anomalies = insights_data.get("anomalies", [])
if anomalies:
    for anomaly in anomalies:
        anomaly_type = anomaly.get("type", "unknown").replace("_", " ").title()
        st.warning(f"**{anomaly_type}**: {anomaly.get('description', anomaly)}")
else:
    st.info("No anomalies detected in the current dataset.")

st.markdown("---")

st.subheader("Value for Money Rankings")

competitive_matrix = load_competitive_matrix()
if not competitive_matrix.empty and "avg_value_for_money" in competitive_matrix.columns:
    ranked = competitive_matrix.sort_values("avg_value_for_money", ascending=False)
    fig_vfm = px.bar(
        ranked,
        x="avg_value_for_money",
        y="brand",
        orientation="h",
        title="Value for Money Score (Sentiment adjusted by Price)",
        color="avg_value_for_money",
        color_continuous_scale="RdYlGn",
    )
    st.plotly_chart(fig_vfm, use_container_width=True)
else:
    st.info("Value for money data not available. Run the competitive analysis pipeline.")

import json
json_str = json.dumps(insights_data, ensure_ascii=False, indent=2)
st.download_button("📥 Download Insights as JSON", json_str, "insights.json", "application/json")
