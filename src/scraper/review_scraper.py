import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.amazon.in"


class AmazonReviewScraper(BaseScraper):
    def __init__(self, api_key: str | None = None, requests_per_minute: int = 30, max_pages: int = 2):
        super().__init__(api_key, requests_per_minute)
        self.max_pages = max_pages

    def _build_review_url(self, asin: str, page: int = 1) -> str:
        return f"{BASE_URL}/product-reviews/{asin}/ref=cm_cr_arp_d_paging_btm_next_{page}?ie=UTF8&reviewerType=all_reviews&pageNumber={page}"

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

    def _parse_helpful_votes(self, text: str | None) -> int:
        if not text:
            return 0
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else 0

    def _parse_review(self, review_el) -> dict | None:
        try:
            review_id = review_el.get("id", "")

            title_el = review_el.select_one("[data-hook='review-title'] span:last-child")
            if not title_el:
                title_el = review_el.select_one("[data-hook='review-title']")
            title = title_el.get_text(strip=True) if title_el else None

            body_el = review_el.select_one("[data-hook='review-body'] span")
            if not body_el:
                body_el = review_el.select_one("[data-hook='review-body']")
            body = body_el.get_text(strip=True) if body_el else ""

            if not title and not body:
                return None

            rating_el = review_el.select_one("[data-hook='review-star-rating'] span, i[data-hook='review-star-rating'] span")
            rating = self._parse_rating(rating_el.get_text(strip=True)) if rating_el else None

            date_el = review_el.select_one("[data-hook='review-date']")
            date = self._parse_date(date_el.get_text(strip=True)) if date_el else None

            verified_el = review_el.select_one("span.a-size-mini")
            verified = False
            if verified_el:
                verified = "verified" in verified_el.get_text(strip=True).lower()

            helpful_el = review_el.select_one("[data-hook='helpful-vote-statement']")
            helpful_votes = self._parse_helpful_votes(helpful_el.get_text(strip=True)) if helpful_el else 0

            return {
                "review_id": review_id,
                "title": title,
                "body": body,
                "rating": rating,
                "date": date,
                "verified_purchase": verified,
                "helpful_votes": helpful_votes,
            }
        except Exception as e:
            logger.warning(f"Error parsing review: {e}")
            return None

    def scrape_product_reviews(self, asin: str, brand: str, max_reviews: int = 5) -> list[dict]:
        reviews = []
        seen_ids = set()

        for page in range(1, self.max_pages + 1):
            url = self._build_review_url(asin, page)
            logger.info(f"Scraping reviews for ASIN {asin} - page {page}")

            try:
                html = self.fetch(url)
            except Exception as e:
                logger.error(f"Failed to fetch reviews for {asin} page {page}: {e}")
                continue

            soup = BeautifulSoup(html, "html.parser")
            review_els = soup.select("[data-hook='review']")

            if not review_els:
                logger.info(f"No more reviews for ASIN {asin} at page {page}")
                break

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

    def scrape(self, products: list[dict], reviews_per_product: int = 5, max_products_per_brand: int = 3) -> list[dict]:
        all_reviews = []
        brand_counts = {}

        for product in products:
            brand = product.get("brand", "Unknown")
            if brand_counts.get(brand, 0) >= max_products_per_brand:
                continue
            asin = product["asin"]
            reviews = self.scrape_product_reviews(asin, brand, reviews_per_product)
            all_reviews.extend(reviews)
            brand_counts[brand] = brand_counts.get(brand, 0) + 1

        self.save_raw(all_reviews, "reviews_raw.json")
        return all_reviews
