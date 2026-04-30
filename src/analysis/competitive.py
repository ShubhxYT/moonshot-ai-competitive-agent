import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"


def compute_price_bands(price: float) -> str:
    if price <= 2000:
        return "Value"
    elif price <= 5000:
        return "Mid-Range"
    elif price <= 10000:
        return "Premium"
    else:
        return "Luxury"


def compute_value_for_money(score: float, price: float) -> float:
    if price <= 0:
        return 0.0
    return round((1 + score) * 1000 / (price / 1000), 2)


def build_competitive_matrix(products_df: pd.DataFrame, reviews_df: pd.DataFrame, sentiment_df: pd.DataFrame, brand_summary_df: pd.DataFrame) -> pd.DataFrame:
    sentiment_brand = sentiment_df.groupby("brand").agg(
        avg_sentiment=("sentiment_score", "mean"),
        review_count_sentiment=("review_id", "count"),
    ).round(3)

    products_df["price_band"] = products_df["price"].apply(compute_price_bands)

    price_band_dist = (
        products_df.groupby(["brand", "price_band"])
        .size()
        .unstack(fill_value=0)
    )

    products_value = products_df.merge(sentiment_df[["asin", "sentiment_score"]], on="asin", how="left")
    products_value["value_for_money"] = products_value.apply(
        lambda r: compute_value_for_money(r.get("sentiment_score", 0), r["price"]), axis=1
    )

    vfm_by_brand = products_value.groupby("brand").agg(
        avg_value_for_money=("value_for_money", "mean"),
    ).round(2)

    matrix = brand_summary_df.set_index("brand_name")
    matrix = matrix.join(sentiment_brand, how="left")
    matrix = matrix.join(price_band_dist, how="left")
    matrix = matrix.join(vfm_by_brand, how="left")
    matrix = matrix.reset_index().rename(columns={"brand_name": "brand"})

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(OUTPUT_DIR / "competitive_matrix.csv", index=False)
    logger.info(f"Competitive matrix saved: {len(matrix)} brands")
    return matrix


def detect_anomalies(products_df: pd.DataFrame, reviews_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> list[dict]:
    anomalies = []

    products_sentiment = products_df.merge(sentiment_df[["asin", "sentiment_score"]], on="asin", how="left")

    high_rating_low_sentiment = products_sentiment[
        (products_sentiment["rating"] >= 4.0) & (products_sentiment["sentiment_score"] < 0.0)
    ]
    for _, row in high_rating_low_sentiment.iterrows():
        anomalies.append({
            "type": "high_rating_negative_sentiment",
            "brand": row["brand"],
            "product": row["title"],
            "rating": row["rating"],
            "sentiment": row["sentiment_score"],
            "description": f"Rating {row['rating']} but sentiment {row['sentiment_score']:.2f}",
        })

    aspect_cols = [c for c in sentiment_df.columns if c.startswith("aspect_")]
    if aspect_cols:
        for brand in sentiment_df["brand"].unique():
            brand_data = sentiment_df[sentiment_df["brand"] == brand]
            for col in aspect_cols:
                aspect_name = col.replace("aspect_", "")
                negative_pct = (brand_data[col] == "negative").mean()
                if negative_pct > 0.4:
                    anomalies.append({
                        "type": "repeated_complaint",
                        "brand": brand,
                        "aspect": aspect_name,
                        "negative_pct": round(negative_pct, 2),
                        "description": f"{brand}: {aspect_name} complaints in {negative_pct:.0%} of reviews",
                    })

    high_discount_low_rating = products_df[
        (products_df["discount_pct"] >= 40) & (products_df["rating"] < 3.5)
    ]
    for _, row in high_discount_low_rating.iterrows():
        anomalies.append({
            "type": "high_discount_low_rating",
            "brand": row["brand"],
            "product": row["title"],
            "discount": row["discount_pct"],
            "rating": row["rating"],
            "description": f"{row['discount_pct']:.0f}% discount but only {row['rating']} stars",
        })

    logger.info(f"Detected {len(anomalies)} anomalies")
    return anomalies


def generate_insights_data(products_df: pd.DataFrame, reviews_df: pd.DataFrame, sentiment_df: pd.DataFrame, brand_summary_df: pd.DataFrame) -> dict:
    matrix = build_competitive_matrix(products_df, reviews_df, sentiment_df, brand_summary_df)
    anomalies = detect_anomalies(products_df, reviews_df, sentiment_df)

    insights_data = {
        "competitive_matrix_path": str(OUTPUT_DIR / "competitive_matrix.csv"),
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "brand_rankings": matrix[["brand", "avg_rating", "avg_sentiment", "avg_price", "avg_discount"]].to_dict("records") if "avg_rating" in matrix.columns else [],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "insights.json", "w") as f:
        json.dump(insights_data, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Insights data saved: {len(anomalies)} anomalies")
    return insights_data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    products_df = pd.read_csv(CLEANED_DIR / "products.csv")
    reviews_df = pd.read_csv(CLEANED_DIR / "reviews.csv")
    brand_summary_df = pd.read_csv(CLEANED_DIR / "brand_summary.csv")
    sentiment_df = pd.read_csv(OUTPUT_DIR / "sentiment_scores.csv")

    generate_insights_data(products_df, reviews_df, sentiment_df, brand_summary_df)
