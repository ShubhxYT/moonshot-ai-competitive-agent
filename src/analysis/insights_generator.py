import json
import logging
import os
from pathlib import Path

import pandas as pd
from groq import Groq

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

INSIGHT_PROMPT = """You are a competitive intelligence analyst specializing in the Indian luggage market. Based on the data below, generate exactly 5 non-obvious, data-backed insights.

Each insight must:
1. Be specific and reference actual numbers from the data
2. Surface something not immediately obvious from raw numbers alone
3. Be actionable for a decision-maker
4. Include a "so what" implication

Available data:
{competitive_data}

Anomalies detected:
{anomalies}

Brand-level summaries:
{brand_summaries}

Theme analysis:
{themes_summary}

Return ONLY a JSON array of 5 objects, each with:
- "insight": string - the main finding (1-2 sentences)
- "evidence": string - specific data points that support this insight
- "implication": string - what a decision-maker should do with this
- "category": one of "pricing", "quality", "positioning", "opportunity", "risk"
"""


class InsightsGenerator:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate_insights(self) -> list[dict]:
        competitive_path = OUTPUT_DIR / "competitive_matrix.csv"
        insights_path = OUTPUT_DIR / "insights.json"
        themes_path = OUTPUT_DIR / "themes.json"
        cleaned_dir = PROJECT_ROOT / "data" / "cleaned"
        brand_summary_path = cleaned_dir / "brand_summary.csv"

        competitive_df = pd.read_csv(competitive_path) if competitive_path.exists() else pd.DataFrame()
        brand_summary_df = pd.read_csv(brand_summary_path) if brand_summary_path.exists() else pd.DataFrame()
        insights_data = {}
        if insights_path.exists():
            with open(insights_path, "r") as f:
                insights_data = json.load(f)
        themes_data = {}
        if themes_path.exists():
            with open(themes_path, "r") as f:
                themes_data = json.load(f)

        competitive_str = competitive_df.to_string() if not competitive_df.empty else "No data"
        anomalies = insights_data.get("anomalies", [])
        anomalies_str = json.dumps(anomalies, indent=2) if anomalies else "No anomalies detected"

        brand_summaries_str = brand_summary_df.to_string() if not brand_summary_df.empty else "No data"

        themes_summary_parts = []
        for brand, data in themes_data.items():
            pros = [p.get("theme", str(p)) if isinstance(p, dict) else str(p) for p in data.get("top_pros", [])]
            cons = [c.get("theme", str(c)) if isinstance(c, dict) else str(c) for c in data.get("top_cons", [])]
            themes_summary_parts.append(f"{brand}: Pros: {', '.join(pros[:3])}; Cons: {', '.join(cons[:3])}")
        themes_str = "\n".join(themes_summary_parts) if themes_summary_parts else "No themes data"

        prompt = INSIGHT_PROMPT.format(
            competitive_data=competitive_str,
            anomalies=anomalies_str,
            brand_summaries=brand_summaries_str,
            themes_summary=themes_str,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)

            if "insights" in result:
                insights = result["insights"]
            elif isinstance(result, list):
                insights = result
            else:
                insights = [result]

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            insights = [
                {
                    "insight": "Insight generation failed. Check logs for details.",
                    "evidence": "API error or data missing",
                    "implication": "Re-run the analysis pipeline",
                    "category": "risk",
                }
            ]

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        insights_data["agent_insights"] = insights
        with open(OUTPUT_DIR / "insights.json", "w") as f:
            json.dump(insights_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Generated {len(insights)} insights")
        return insights


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generator = InsightsGenerator()
    insights = generator.generate_insights()
    for i, insight in enumerate(insights, 1):
        print(f"\n{i}. {insight.get('insight', insight)}")
