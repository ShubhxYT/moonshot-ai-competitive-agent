import json
import logging
import os
from pathlib import Path

import pandas as pd
from groq import Groq

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

THEME_PROMPT = """Analyze these aggregated review sentiment data for the brand "{brand}" and return ONLY a JSON object with:
- "top_pros": array of 5 objects, each with "theme" (string) and "frequency" (estimated count)
- "top_cons": array of 5 objects, each with "theme" (string) and "frequency" (estimated count)
- "summary": a 2-3 sentence summary of overall customer sentiment toward this brand
- "aspect_sentiment": object with aspect names as keys and average sentiment as values

Data:
- Average star rating: {avg_rating}
- Average sentiment score: {avg_sentiment}
- Total reviews: {total_reviews}
- Key phrases from reviews: {key_phrases}
- Aspect-level sentiments: {aspects}

Return ONLY the JSON object, no other text."""


class ThemeExtractor:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = Groq(api_key=api_key)
        self.model = model

    def _call_groq(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def extract_brand_themes(self, brand: str, sentiment_df: pd.DataFrame) -> dict:
        brand_reviews = sentiment_df[sentiment_df["brand"] == brand]

        if brand_reviews.empty:
            return {"brand": brand, "top_pros": [], "top_cons": [], "summary": "", "aspect_sentiment": {}}

        key_phrases = brand_reviews["key_phrases"].dropna().tolist()
        key_phrases_str = "; ".join([p for phrase in key_phrases for p in phrase.split("|")][:50])

        aspect_cols = [c for c in brand_reviews.columns if c.startswith("aspect_")]
        aspects = {}
        for col in aspect_cols:
            aspect_name = col.replace("aspect_", "")
            vc = brand_reviews[col].value_counts()
            dominant = vc.index[0] if len(vc) > 0 else "neutral"
            aspects[aspect_name] = dominant

        prompt = THEME_PROMPT.format(
            brand=brand,
            avg_rating=round(brand_reviews["rating"].mean(), 2) if "rating" in brand_reviews.columns else 0,
            avg_sentiment=round(brand_reviews["sentiment_score"].mean(), 3),
            total_reviews=len(brand_reviews),
            key_phrases=key_phrases_str,
            aspects=json.dumps(aspects),
        )

        try:
            response = self._call_groq(prompt)
            themes = json.loads(response)
            themes["brand"] = brand
            return themes
        except Exception as e:
            logger.error(f"Theme extraction failed for {brand}: {e}")
            return {
                "brand": brand,
                "top_pros": [],
                "top_cons": [],
                "summary": f"Theme extraction failed for {brand}",
                "aspect_sentiment": aspects,
            }

    def run(self, sentiment_df: pd.DataFrame, reviews_df: pd.DataFrame) -> dict:
        sentiment_with_rating = sentiment_df.merge(
            reviews_df[["review_id", "rating"]], on="review_id", how="left"
        )

        brands = sentiment_df["brand"].unique()
        all_themes = {}

        for brand in brands:
            logger.info(f"Extracting themes for {brand}...")
            all_themes[brand] = self.extract_brand_themes(brand, sentiment_with_rating)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_DIR / "themes.json", "w") as f:
            json.dump(all_themes, f, ensure_ascii=False, indent=2)

        logger.info(f"Theme extraction complete for {len(all_themes)} brands")
        return all_themes
