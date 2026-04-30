import logging
import re
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from src.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.amazon.in"


class AmazonProductScraper(BaseScraper):
    def __init__(self, api_key: str | None = None, requests_per_minute: int = 30, max_pages: int = 1):
        super().__init__(api_key, requests_per_minute)
        self.max_pages = max_pages

    def _build_search_url(self, query: str, page: int = 1) -> str:
        encoded_query = quote_plus(query)
        return f"{BASE_URL}/s?k={encoded_query}&page={page}"

    def _parse_price(self, price_text: str | None) -> float | None:
        if not price_text:
            return None
        cleaned = re.sub(r"[^\d.]", "", price_text.replace(",", ""))
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _parse_rating(self, rating_text: str | None) -> float | None:
        if not rating_text:
            return None
        match = re.search(r"([\d.]+)\s*out\s*of\s*5", rating_text)
        if match:
            return float(match.group(1))
        try:
            return float(rating_text.strip())
        except ValueError:
            return None

    def _parse_review_count(self, count_text: str | None) -> int | None:
        if not count_text:
            return None
        match = re.search(r"[\d,]+", count_text.replace(",", ""))
        if match:
            return int(match.group().replace(",", ""))
        return None

    def _parse_discount(self, discount_text: str | None) -> float | None:
        if not discount_text:
            return None
        match = re.search(r"(\d+)%", discount_text)
        if match:
            return float(match.group(1))
        return None

    def _parse_product_card(self, card) -> dict | None:
        try:
            asin = card.get("data-asin", "")
            if not asin:
                return None

            title_el = card.select_one("h2 a span")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                title_el = card.select_one("h2 .a-text-normal")
                title = title_el.get_text(strip=True) if title_el else None

            link_el = card.select_one("h2 a")
            url = urljoin(BASE_URL, link_el["href"]) if link_el and link_el.get("href") else None

            price_el = card.select_one("span.a-price span.a-offscreen")
            price = self._parse_price(price_el.get_text(strip=True)) if price_el else None
            if price is None:
                price_el_alt = card.select_one("span.a-price-whole")
                price = self._parse_price(price_el_alt.get_text(strip=True)) if price_el_alt else None

            mrp_el = card.select_one("span.a-text-price span.a-offscreen")
            mrp = self._parse_price(mrp_el.get_text(strip=True)) if mrp_el else None

            discount_el = card.select_one("span.a-badge-text")
            discount_text = discount_el.get_text(strip=True) if discount_el else None
            if discount_text:
                discount = self._parse_discount(discount_text)
            else:
                discount = None

            if price and mrp and mrp > price and discount is None:
                discount = round((1 - price / mrp) * 100, 1)

            rating_el = card.select_one("i.a-icon-star-small span.a-icon-alt")
            rating = self._parse_rating(rating_el.get_text(strip=True)) if rating_el else None
            if rating is None:
                rating_el = card.select_one("span.a-icon-alt")
                rating = self._parse_rating(rating_el.get_text(strip=True)) if rating_el else None

            review_count_el = card.select_one("span.a-size-base[href*='reviews']")
            review_count = self._parse_review_count(review_count_el.get_text(strip=True)) if review_count_el else None
            if review_count is None:
                review_count_el = card.select_one("a span.a-size-base")
                review_count = self._parse_review_count(review_count_el.get_text(strip=True)) if review_count_el else None

            image_el = card.select_one("img.s-image")
            image_url = image_el["src"] if image_el else None

            availability_el = card.select_one("span.a-size-base.a-color-price")
            availability = availability_el.get_text(strip=True) if availability_el else "Available"

            return {
                "asin": asin,
                "title": title,
                "url": url,
                "price": price,
                "mrp": mrp,
                "discount_pct": discount,
                "rating": rating,
                "review_count": review_count,
                "image_url": image_url,
                "availability": availability,
                "brand": None,
            }
        except Exception as e:
            logger.warning(f"Error parsing product card: {e}")
            return None

    def scrape_brand(self, brand_name: str, search_query: str) -> list[dict]:
        products = []
        seen_asins = set()

        for page in range(1, self.max_pages + 1):
            url = self._build_search_url(search_query, page)
            logger.info(f"Scraping {brand_name} - page {page}: {url}")

            try:
                html = self.fetch(url)
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                continue

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div[data-component-type='s-search-result']")
            if not cards:
                cards = soup.select("div.s-result-item[data-asin]")

            if not cards:
                logger.warning(f"No product cards found for {brand_name} page {page}")
                break

            for card in cards:
                product = self._parse_product_card(card)
                if product and product["asin"] not in seen_asins:
                    product["brand"] = brand_name
                    seen_asins.add(product["asin"])
                    products.append(product)

            if len(seen_asins) >= 3:
                break

        logger.info(f"Scraped {len(products)} products for {brand_name}")
        return products

    def scrape(self, brands: list[dict]) -> list[dict]:
        all_products = []
        for brand in brands:
            products = self.scrape_brand(brand["name"], brand["search_query"])
            all_products.extend(products)

        self.save_raw(all_products, "products_raw.json")
        return all_products
