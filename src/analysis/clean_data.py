import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"


def load_raw_products() -> list[dict]:
    filepath = RAW_DIR / "products_raw.json"
    if not filepath.exists():
        raise FileNotFoundError(f"Products file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_raw_reviews() -> list[dict]:
    filepath = RAW_DIR / "reviews_raw.json"
    if not filepath.exists():
        raise FileNotFoundError(f"Reviews file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_products(raw_products: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(raw_products)

    df = df.drop_duplicates(subset=["asin"], keep="first")
    df = df.dropna(subset=["asin", "title"])

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["mrp"] = pd.to_numeric(df["mrp"], errors="coerce")

    df.loc[df["discount_pct"].isna() & df["price"].notna() & df["mrp"].notna() & (df["mrp"] > 0), "discount_pct"] = (
        (1 - df["price"] / df["mrp"]) * 100
    ).round(1)

    df.loc[(df["mrp"].isna() | (df["mrp"] == 0)) & df["price"].notna(), "mrp"] = df["price"]
    df.loc[df["price"].notna() & df["mrp"].notna() & (df["mrp"] < df["price"]), "mrp"] = df["price"]
    df.loc[df["discount_pct"].isna(), "discount_pct"] = 0.0

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").astype("Int64")

    df = df[df["price"].notna() & (df["price"] > 0)]

    df = df.reset_index(drop=True)
    logger.info(f"Cleaned products: {len(df)} rows from {len(raw_products)} raw")
    return df


def clean_reviews(raw_reviews: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(raw_reviews)

    df = df.drop_duplicates(subset=["review_id"], keep="first")
    df = df.dropna(subset=["review_id"])

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df[df["rating"].notna()]

    df["verified_purchase"] = df["verified_purchase"].fillna(False).astype(bool)
    df["helpful_votes"] = pd.to_numeric(df.get("helpful_votes", 0), errors="coerce").fillna(0).astype(int)

    df = df[df["body"].notna() & (df["body"].str.len() > 10)]

    df = df.reset_index(drop=True)
    logger.info(f"Cleaned reviews: {len(df)} rows from {len(raw_reviews)} raw")
    return df


def create_brand_summary(products_df: pd.DataFrame, reviews_df: pd.DataFrame) -> pd.DataFrame:
    product_stats = (
        products_df.groupby("brand")
        .agg(
            product_count=("asin", "count"),
            avg_price=("price", "mean"),
            median_price=("price", "median"),
            min_price=("price", "min"),
            max_price=("price", "max"),
            avg_mrp=("mrp", "mean"),
            avg_discount=("discount_pct", "mean"),
            avg_rating=("rating", "mean"),
            total_reviews=("review_count", "sum"),
        )
        .round(2)
    )

    review_stats = (
        reviews_df.groupby("brand")
        .agg(
            scraped_review_count=("review_id", "count"),
            avg_review_rating=("rating", "mean"),
            verified_review_pct=("verified_purchase", "mean"),
        )
        .round(2)
    )

    brand_summary = product_stats.join(review_stats, how="left").reset_index()
    brand_summary = brand_summary.rename(columns={"brand": "brand_name"})

    logger.info(f"Brand summary: {len(brand_summary)} brands")
    return brand_summary


def run_cleaning():
    logger.info("Starting data cleaning pipeline...")

    raw_products = load_raw_products()
    raw_reviews = load_raw_reviews()

    products_df = clean_products(raw_products)
    reviews_df = clean_reviews(raw_reviews)
    brand_summary_df = create_brand_summary(products_df, reviews_df)

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    products_df.to_csv(CLEANED_DIR / "products.csv", index=False)
    products_df.to_parquet(CLEANED_DIR / "products.parquet", index=False)
    reviews_df.to_csv(CLEANED_DIR / "reviews.csv", index=False)
    reviews_df.to_parquet(CLEANED_DIR / "reviews.parquet", index=False)
    brand_summary_df.to_csv(CLEANED_DIR / "brand_summary.csv", index=False)

    logger.info(f"Cleaned data saved to {CLEANED_DIR}")
    return products_df, reviews_df, brand_summary_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_cleaning()
