import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Luggage Brand Intelligence — Amazon India",
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded",
)

overview = st.Page("pages/01_Overview.py", title="Overview", icon="📊")
comparison = st.Page("pages/02_Brand_Comparison.py", title="Brand Comparison", icon="⚖️")
drilldown = st.Page("pages/03_Product_Drilldown.py", title="Product Drilldown", icon="🔍")
insights = st.Page("pages/04_Agent_Insights.py", title="Agent Insights", icon="🤖")

pg = st.navigation([overview, comparison, drilldown, insights])
pg.run()
