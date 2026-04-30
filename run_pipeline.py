import argparse
import logging
import os
import sys
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent


def load_config() -> dict:
    config_path = PROJECT_ROOT / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def step_scrape_products(config: dict, api_key: str | None = None):
    from src.scraper.amazon_scraper import AmazonProductScraper

    scraper = AmazonProductScraper(
        api_key=api_key,
        requests_per_minute=config["scraping"]["requests_per_minute"],
        max_pages=config["scraping"]["max_search_pages"],
        products_per_brand=config["scraping"]["products_per_brand"],
    )
    products = scraper.scrape(config["brands"])
    logger.info(f"Step 1 complete: {len(products)} products scraped")
    return products


def step_scrape_reviews(config: dict, api_key: str | None = None):
    import json
    from src.scraper.review_scraper import AmazonReviewScraper

    products_path = PROJECT_ROOT / "data" / "raw" / "products_raw.json"
    with open(products_path, "r") as f:
        products = json.load(f)

    scraper = AmazonReviewScraper(
        api_key=api_key,
        requests_per_minute=config["scraping"]["requests_per_minute"],
    )
    reviews = scraper.scrape(
        products,
        reviews_per_product=config["scraping"]["reviews_per_product"],
        max_products_per_brand=config["scraping"]["products_per_brand"],
    )
    logger.info(f"Step 2 complete: {len(reviews)} reviews scraped")
    return reviews


def step_clean_data():
    from src.analysis.clean_data import run_cleaning
    results = run_cleaning()
    logger.info(f"Step 3 complete: {len(results[0])} products, {len(results[1])} reviews cleaned")
    return results


def step_sentiment(config: dict):
    import pandas as pd
    from src.analysis.sentiment import SentimentAnalyzer

    reviews_df = pd.read_csv(PROJECT_ROOT / "data" / "cleaned" / "reviews.csv")
    analyzer = SentimentAnalyzer(
        model=config["sentiment"]["model"],
        batch_size=config["sentiment"]["batch_size"],
    )
    sentiment_df = analyzer.run(reviews_df)
    logger.info(f"Step 4 complete: {len(sentiment_df)} reviews analyzed")
    return sentiment_df


def step_themes(config: dict):
    import pandas as pd
    from src.analysis.themes import ThemeExtractor

    sentiment_df = pd.read_csv(PROJECT_ROOT / "data" / "outputs" / "sentiment_scores.csv")
    reviews_df = pd.read_csv(PROJECT_ROOT / "data" / "cleaned" / "reviews.csv")
    extractor = ThemeExtractor(model=config["sentiment"]["model"])
    themes = extractor.run(sentiment_df, reviews_df)
    logger.info(f"Step 5 complete: {len(themes)} brands processed")
    return themes


def step_competitive():
    import pandas as pd
    from src.analysis.competitive import generate_insights_data

    products_df = pd.read_csv(PROJECT_ROOT / "data" / "cleaned" / "products.csv")
    reviews_df = pd.read_csv(PROJECT_ROOT / "data" / "cleaned" / "reviews.csv")
    brand_summary_df = pd.read_csv(PROJECT_ROOT / "data" / "cleaned" / "brand_summary.csv")
    sentiment_df = pd.read_csv(PROJECT_ROOT / "data" / "outputs" / "sentiment_scores.csv")
    insights = generate_insights_data(products_df, reviews_df, sentiment_df, brand_summary_df)
    logger.info("Step 6 complete: Competitive matrix and insights generated")
    return insights


def step_insights():
    from src.analysis.insights_generator import InsightsGenerator

    generator = InsightsGenerator()
    insights_list = generator.generate_insights()
    logger.info(f"Step 7 complete: {len(insights_list)} insights generated")
    return insights_list


STEPS = {
    "scrape-products": ("Scrape product listings", step_scrape_products),
    "scrape-reviews": ("Scrape product reviews", step_scrape_reviews),
    "clean": ("Clean and structure data", step_clean_data),
    "sentiment": ("Run sentiment analysis", step_sentiment),
    "themes": ("Extract themes", step_themes),
    "competitive": ("Build competitive analysis", step_competitive),
    "insights": ("Generate AI insights", step_insights),
}


def main():
    parser = argparse.ArgumentParser(description="Run the competitive intelligence pipeline")
    parser.add_argument("--step", choices=list(STEPS.keys()), help="Run a specific step")
    parser.add_argument("--all", action="store_true", help="Run all steps in order")
    parser.add_argument("--from", choices=list(STEPS.keys()), dest="from_step", help="Run from this step onwards")
    parser.add_argument("--no-api", action="store_true", help="Skip scraping API (direct requests)")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    config = load_config()
    api_key = os.getenv("SCRAPER_API_KEY") if not args.no_api else None

    if args.all:
        step_order = list(STEPS.keys())
    elif args.from_step:
        step_idx = list(STEPS.keys()).index(args.from_step)
        step_order = list(STEPS.keys())[step_idx:]
    elif args.step:
        step_order = [args.step]
    else:
        parser.print_help()
        return

    for step_name in step_order:
        description, step_fn = STEPS[step_name]
        logger.info(f"Running: {description} ({step_name})")
        try:
            if step_name in ("scrape-products", "scrape-reviews"):
                step_fn(config, api_key)
            elif step_name in ("sentiment", "themes"):
                step_fn(config)
            else:
                step_fn()
        except Exception as e:
            logger.error(f"Step {step_name} failed: {e}")
            sys.exit(1)

    logger.info("Pipeline complete!")


if __name__ == "__main__":
    main()
