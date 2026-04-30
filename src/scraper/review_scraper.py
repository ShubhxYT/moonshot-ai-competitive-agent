import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.amazon.in"


class AmazonReviewScraper(BaseScraper):
    def __init__(self, api_key: str | None = None, requests_per_minute: int = 30):
        super().__init__(api_key, requests_per_minute)

    def _build_product_url(self, asin: str) -> str:
        return f"{BASE_URL}/dp/{asin}"

    def _parse_date(self, date_text: str | None) -> str | None:
        if not date_text:
            return None
        date_text = date_text.replace("Reviewed in India on ", "").strip()
        return date_text

    def _parse_rating(self, rating_text: str | None) -> int | None:
        if not rating_text:
            return None
        match = re.search(r"(\d)\.0\s*out\s*of\s*5", rating_text)
        if match:
            return int(match.group(1))
        match = re.search(r"(\d)", rating_text)
        if match:
            return int(match.group(1))
        return None

    def _parse_title(self, review_el) -> str | None:
        try:
            el = review_el.select_one("[data-hook='reviewTitle']")
            if el:
                return el.get_text(strip=True)
            el = review_el.select_one("[data-hook='review-title']")
            if el:
                spans = el.find_all("span", recursive=False)
                if spans:
                    return spans[-1].get_text(strip=True)
                return el.get_text(strip=True)
        except Exception:
            return None

    def _parse_body(self, review_el) -> str:
        try:
            el = review_el.select_one("[data-hook='reviewRichContentContainer']")
            if el:
                return el.get_text(strip=True)
            el = review_el.select_one("[data-hook='review-body']")
            if el:
                return el.get_text(strip=True)
        except Exception:
            pass
        return ""

    def _parse_review(self, review_el) -> dict | None:
        try:
            review_id = review_el.get("id", "")
            title = self._parse_title(review_el)
            body = self._parse_body(review_el)

            if not title and not body:
                return None

            rating_el = review_el.select_one("[data-hook='review-star-rating']")
            rating = self._parse_rating(rating_el.get_text(strip=True)) if rating_el else None

            date_el = review_el.select_one("[data-hook='review-date']")
            date = self._parse_date(date_el.get_text(strip=True)) if date_el else None

            verified_el = review_el.select_one("[data-hook='avp-badge'], [data-hook='avp-badge-linkless']")
            verified = bool(verified_el)

            return {
                "review_id": review_id,
                "title": title,
                "body": body,
                "rating": rating,
                "date": date,
                "verified_purchase": verified,
                "helpful_votes": 0,
            }
        except Exception as e:
            logger.warning(f"Error parsing review: {e}")
            return None

    def scrape_product_reviews(self, asin: str, brand: str, max_reviews: int = 5) -> list[dict]:
        reviews = []
        seen_ids = set()

        url = self._build_product_url(asin)
        logger.info(f"Scraping reviews for ASIN {asin} from product page")

        try:
            html = self.fetch(url)
        except Exception as e:
            logger.error(f"Failed to fetch product page for {asin}: {e}")
            return []

        soup = BeautifulSoup(html, "html.parser")
        review_els = soup.select("[data-hook='review']")

        if not review_els:
            logger.info(f"No reviews found for ASIN {asin}")
            return []

        for review_el in review_els:
            review = self._parse_review(review_el)
            if review and review["review_id"] not in seen_ids:
                review["asin"] = asin
                review["brand"] = brand
                if review.get("body") and len(review["body"].strip()) > 10:
                    seen_ids.add(review["review_id"])
                    reviews.append(review)

            if len(reviews) >= max_reviews:
                break

        logger.info(f"Scraped {len(reviews)} reviews for ASIN {asin}")
        return reviews

    def scrape(self, products: list[dict], reviews_per_product: int = 5, max_products_per_brand: int | None = None) -> list[dict]:
        all_reviews = []
        brand_counts = {}

        for product in products:
            brand = product.get("brand", "Unknown")
            if max_products_per_brand is not None and brand_counts.get(brand, 0) >= max_products_per_brand:
                continue
            asin = product["asin"]
            reviews = self.scrape_product_reviews(asin, brand, reviews_per_product)
            all_reviews.extend(reviews)
            brand_counts[brand] = brand_counts.get(brand, 0) + 1

        self.save_raw(all_reviews, "reviews_raw.json")
        return all_reviews


if __name__ == "__main__":
    import json
    import os
    from pathlib import Path
    import yaml
    from dotenv import load_dotenv

    load_dotenv()
    config_path = Path(__file__).resolve().parents[2] / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    products_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "products_raw.json"
    with open(products_path) as f:
        products = json.load(f)

    scraper = AmazonReviewScraper(
        api_key=os.getenv("SCRAPER_API_KEY"),
        requests_per_minute=config["scraping"]["requests_per_minute"],
    )
    reviews = scraper.scrape(
        products,
        reviews_per_product=config["scraping"]["reviews_per_product"],
        max_products_per_brand=config["scraping"]["products_per_brand"],
    )
    print(f"Scraped {len(reviews)} reviews")
