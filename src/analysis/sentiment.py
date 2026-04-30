import json
import logging
import os
import time
from pathlib import Path

import pandas as pd
from groq import Groq

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

ASPECTS = ["wheels", "handle", "zipper", "material", "size", "durability"]

SENTIMENT_PROMPT = """Analyze this product review and return ONLY a JSON object with these fields:
- "sentiment_score": float from -1.0 (very negative) to 1.0 (very positive)
- "aspects": object with keys for each relevant aspect from [{aspects}] and values of "positive", "negative", or "neutral". Only include aspects actually mentioned.
- "key_phrases": array of 1-3 short phrases that capture the main sentiment

Review title: {title}
Review body: {body}

Return ONLY the JSON object, no other text."""

BATCH_SENTIMENT_PROMPT = """Analyze these {count} product reviews and return ONLY a JSON array where each element has:
- "sentiment_score": float from -1.0 to 1.0
- "aspects": object with aspect names from [{aspects}] as keys and "positive"/"negative"/"neutral" as values (only include mentioned aspects)
- "key_phrases": array of 1-3 short sentiment phrases

Reviews:
{reviews}

Return ONLY the JSON array, no other text."""


class SentimentAnalyzer:
    def __init__(self, model: str = "llama-3.3-70b-versatile", batch_size: int = 10):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = Groq(api_key=api_key)
        self.model = model
        self.batch_size = batch_size
        self.cache_path = OUTPUT_DIR / "sentiment_cache.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if self.cache_path.exists():
            with open(self.cache_path, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f)

    def _call_groq(self, prompt: str, max_tokens: int = 4096) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def _call_groq_array(self, prompt: str, max_tokens: int = 4096) -> str:
        """Call Groq without json_object constraint so the model can return a bare JSON array."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    def analyze_single(self, review_title: str, review_body: str, review_id: str = "") -> dict:
        if review_id and review_id in self.cache:
            return self.cache[review_id]

        prompt = SENTIMENT_PROMPT.format(
            aspects=", ".join(ASPECTS),
            title=review_title or "No title",
            body=review_body or "No body",
        )

        result = self._call_groq(prompt)

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse sentiment result for {review_id}")
            parsed = {"sentiment_score": 0.0, "aspects": {}, "key_phrases": []}

        if review_id:
            self.cache[review_id] = parsed
            self._save_cache()

        return parsed

    def analyze_batch(self, reviews: list[dict]) -> list[dict]:
        results = [None] * len(reviews)
        uncached_indices = []
        uncached_reviews_text = []

        for i, review in enumerate(reviews):
            rid = review.get("review_id", "")
            if rid and rid in self.cache:
                results[i] = self.cache[rid]
            else:
                uncached_indices.append(i)
                uncached_reviews_text.append(
                    f"Review {len(uncached_reviews_text) + 1}: Title: {review.get('title', 'No title')}. Body: {review.get('body', 'No body')}"
                )

        if uncached_reviews_text:
            for batch_start in range(0, len(uncached_reviews_text), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(uncached_reviews_text))
                batch_text = "\n\n".join(uncached_reviews_text[batch_start:batch_end])
                batch_indices = uncached_indices[batch_start:batch_end]

                prompt = BATCH_SENTIMENT_PROMPT.format(
                    count=batch_end - batch_start,
                    aspects=", ".join(ASPECTS),
                    reviews=batch_text,
                )

                try:
                    response = self._call_groq_array(prompt)
                    parsed = json.loads(response)
                    if isinstance(parsed, dict):
                        parsed = parsed.get("results", parsed.get("reviews", [parsed]))

                    for j, idx in enumerate(batch_indices):
                        if isinstance(parsed, list) and j < len(parsed):
                            results[idx] = parsed[j]
                            rid = reviews[idx].get("review_id", "")
                            if rid:
                                self.cache[rid] = parsed[j]
                        else:
                            results[idx] = {"sentiment_score": 0.0, "aspects": {}, "key_phrases": []}

                except Exception as e:
                    logger.error(f"Batch sentiment analysis failed: {e}")
                    for idx in batch_indices:
                        results[idx] = {"sentiment_score": 0.0, "aspects": {}, "key_phrases": []}

                time.sleep(1)

        self._save_cache()
        return results

    def run(self, reviews_df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"Running sentiment analysis on {len(reviews_df)} reviews...")
        reviews = reviews_df[["review_id", "title", "body"]].to_dict("records")
        results = self.analyze_batch(reviews)

        sentiment_df = pd.DataFrame(
            [
                {
                    "review_id": r.get("review_id", ""),
                    "asin": reviews_df.iloc[i].get("asin", ""),
                    "brand": reviews_df.iloc[i].get("brand", ""),
                    "sentiment_score": results[i].get("sentiment_score", 0.0),
                    **{f"aspect_{k}": v for k, v in results[i].get("aspects", {}).items()},
                    "key_phrases": "|".join(results[i].get("key_phrases", [])),
                }
                for i, r in enumerate(reviews)
            ]
        )

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        sentiment_df.to_csv(OUTPUT_DIR / "sentiment_scores.csv", index=False)
        logger.info(f"Sentiment analysis complete: {len(sentiment_df)} reviews scored")
        return sentiment_df


if __name__ == "__main__":
    import yaml
    from dotenv import load_dotenv

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    load_dotenv()
    config_path = PROJECT_ROOT / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    reviews_df = pd.read_csv(PROJECT_ROOT / "data" / "cleaned" / "reviews.csv")
    analyzer = SentimentAnalyzer(
        model=config["sentiment"]["model"],
        batch_size=config["sentiment"]["batch_size"],
    )
    sentiment_df = analyzer.run(reviews_df)
    print(f"Scored {len(sentiment_df)} reviews → data/outputs/sentiment_scores.csv")
