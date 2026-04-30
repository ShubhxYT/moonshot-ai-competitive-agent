# Competitive Intelligence Dashboard — Implementation

## Goal

Build an interactive Streamlit dashboard that scrapes, analyzes, and visualizes pricing and review sentiment data for 6 luggage brands on Amazon India.

## Prerequisites

- [x] Python 3.11+ installed
- [ ] Git initialized: `git init`
- [ ] Branch `competitive-intelligence-dashboard` checked out from `main`
- [ ] ScraperAPI key from https://scraperapi.com (free tier: 1000 requests/month)
- [ ] Groq API key from https://console.groq.com (free tier available)

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| Scraping | requests + ScraperAPI + BeautifulSoup4 | Latest |
| Data | Pandas | 2.x |
| Dashboard | Streamlit | 1.36+ |
| Charts | Plotly | 5.x |
| LLM | Groq (llama-3.3-70b-versatile) | Latest |
| Config | PyYAML + python-dotenv | Latest |

## Directory Structure (Final)

```
Munshot/
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── .env.example
├── config.yaml
├── README.md
├── src/
│   ├── __init__.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── amazon_scraper.py
│   │   ├── review_scraper.py
│   │   └── utils.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── clean_data.py
│   │   ├── sentiment.py
│   │   ├── themes.py
│   │   ├── competitive.py
│   │   └── insights_generator.py
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py
│       ├── components.py
│       ├── styles.css
│       └── pages/
│           ├── 01_Overview.py
│           ├── 02_Brand_Comparison.py
│           ├── 03_Product_Drilldown.py
│           └── 04_Agent_Insights.py
├── data/
│   ├── raw/
│   ├── cleaned/
│   └── outputs/
├── docs/
│   ├── architecture.md
│   └── limitations.md
└── plans/
    └── competitive-intelligence-dashboard/
        ├── plan.md
        └── implementation.md
```

---

## Steps

### Step 1: Project scaffolding and dependency setup

**Files:** `pyproject.toml`, `requirements.txt`, `.gitignore`, `.env.example`, `config.yaml`, `src/__init__.py`, `src/scraper/__init__.py`, `src/analysis/__init__.py`, `src/dashboard/__init__.py`, all `data/` directories

- [x] Create `pyproject.toml`
  ```toml
  [project]
  name = "munshot-competitive-intel"
  version = "0.1.0"
  description = "Competitive intelligence dashboard for luggage brands on Amazon India"
  requires-python = ">=3.11"
  dependencies = [
      "requests>=2.31",
      "pandas>=2.1",
      "streamlit>=1.36",
      "plotly>=5.18",
      "beautifulsoup4>=4.12",
      "groq>=0.5",
      "pyyaml>=6.0",
      "python-dotenv>=1.0",
  ]

  [project.optional-dependencies]
  dev = [
      "pytest>=7.4",
      "ruff>=0.1",
  ]

  [tool.ruff]
  line-length = 120
  target-version = "py311"

  [tool.ruff.lint]
  select = ["E", "F", "I"]
  ```

- [x] Create `requirements.txt`
  ```
  requests>=2.31
  pandas>=2.1
  streamlit>=1.36
  plotly>=5.18
  beautifulsoup4>=4.12
  groq>=0.5
  pyyaml>=6.0
  python-dotenv>=1.0
  ```

- [x] Create `.gitignore`
  ```
  __pycache__/
  *.py[cod]
  *.egg-info/
  .env
  data/raw/
  data/cleaned/
  data/outputs/
  !data/raw/.gitkeep
  !data/cleaned/.gitkeep
  !data/outputs/.gitkeep
  .venv/
  venv/
  .DS_Store
  *.log
  .streamlit/secrets.toml
  ```

- [x] Create `.env.example`
  ```
  SCRAPER_API_KEY=your_scraperapi_key_here
  GROQ_API_KEY=your_groq_api_key_here
  ```

- [x] Create `config.yaml`
  ```yaml
  brands:
    - name: Safari
      search_query: "Safari luggage"
    - name: Skybags
      search_query: "Skybags luggage"
    - name: American Tourister
      search_query: "American Tourister suitcase"
    - name: VIP
      search_query: "VIP luggage"
    - name: Aristocrat
      search_query: "Aristocrat luggage"
    - name: Nasher Miles
      search_query: "Nasher Miles luggage"

  scraping:
    products_per_brand: 10
    reviews_per_product: 50
    max_search_pages: 3
    max_review_pages: 5
    requests_per_minute: 30
    retry_attempts: 3
    retry_delay_seconds: 2

  sentiment:
    batch_size: 10
    model: "llama-3.3-70b-versatile"
    max_tokens_per_batch: 4096

  dashboard:
    title: "Luggage Brand Intelligence — Amazon India"
    theme: "wide"
  ```

- [x] Create directory structure
  ```bash
  mkdir -p src/scraper src/analysis src/dashboard/pages data/raw data/cleaned data/outputs docs && touch src/__init__.py src/scraper/__init__.py src/analysis/__init__.py src/dashboard/__init__.py data/raw/.gitkeep data/cleaned/.gitkeep data/outputs/.gitkeep
  ```

- [x] Create `.env` from template (add your real keys)
  ```bash
  cp .env.example .env
  ```

- [x] Install dependencies
  ```bash
  uv sync
  ```

- [x] Verify: `uv sync` succeeds without errors
- [x] Verify: Project directory matches the directory structure above

STOP AND COMMIT

---

### Step 2: Amazon India scraper — product listing

**Files:** `src/scraper/utils.py`, `src/scraper/base.py`, `src/scraper/amazon_scraper.py`

- [x] Create `src/scraper/utils.py`
  ```python
  import logging
  import time

  import requests
  from requests.adapters import HTTPAdapter
  from urllib3.util.retry import Retry

  logger = logging.getLogger(__name__)


  def create_session(retries: int = 3, backoff_factor: float = 1.0) -> requests.Session:
      session = requests.Session()
      retry_strategy = Retry(
          total=retries,
          backoff_factor=backoff_factor,
          status_forcelist=[429, 500, 502, 503, 504],
      )
      adapter = HTTPAdapter(max_retries=retry_strategy)
      session.mount("https://", adapter)
      session.mount("http://", adapter)
      return session


  class RateLimiter:
      def __init__(self, requests_per_minute: int = 30):
          self.min_interval = 60.0 / requests_per_minute
          self.last_request_time = 0.0

      def wait(self):
          elapsed = time.time() - self.last_request_time
          if elapsed < self.min_interval:
              time.sleep(self.min_interval - elapsed)
          self.last_request_time = time.time()


  def fetch_via_scraper_api(url: str, api_key: str, session: requests.Session = None) -> str:
      if session is None:
          session = create_session()
      api_url = "http://api.scraperapi.com/"
      params = {"api_key": api_key, "url": url, "country_code": "in"}
      logger.info(f"Fetching via ScraperAPI: {url}")
      response = session.get(api_url, params=params, timeout=60)
      response.raise_for_status()
      return response.text


  def fetch_direct(url: str, session: requests.Session = None) -> str:
      if session is None:
          session = create_session()
      headers = {
          "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
          "Accept-Language": "en-IN,en;q=0.9",
          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      }
      logger.info(f"Fetching directly: {url}")
      response = session.get(url, headers=headers, timeout=30)
      response.raise_for_status()
      return response.text
  ```

- [x] Create `src/scraper/base.py`
  ```python
  import json
  import logging
  from abc import ABC, abstractmethod
  from pathlib import Path

  from src.scraper.utils import RateLimiter, create_session, fetch_via_scraper_api, fetch_direct

  logger = logging.getLogger(__name__)

  DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


  class BaseScraper(ABC):
      def __init__(self, api_key: str | None = None, requests_per_minute: int = 30):
          self.api_key = api_key
          self.session = create_session()
          self.rate_limiter = RateLimiter(requests_per_minute)
          self.use_api = api_key is not None

      def fetch(self, url: str) -> str:
          self.rate_limiter.wait()
          if self.use_api:
              return fetch_via_scraper_api(url, self.api_key, self.session)
          return fetch_direct(url, self.session)

      def save_raw(self, data: list[dict], filename: str):
          DATA_DIR.mkdir(parents=True, exist_ok=True)
          filepath = DATA_DIR / filename
          with open(filepath, "w", encoding="utf-8") as f:
              json.dump(data, f, ensure_ascii=False, indent=2)
          logger.info(f"Saved {len(data)} records to {filepath}")

      @abstractmethod
      def scrape(self, **kwargs) -> list[dict]:
          ...
  ```

- [x] Create `src/scraper/amazon_scraper.py`
  ```python
  import logging
  import re
  from urllib.parse import quote_plus, urljoin

  from bs4 import BeautifulSoup

  from src.scraper.base import BaseScraper

  logger = logging.getLogger(__name__)

  BASE_URL = "https://www.amazon.in"


  class AmazonProductScraper(BaseScraper):
      def __init__(self, api_key: str | None = None, requests_per_minute: int = 30, max_pages: int = 3):
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

              if len(seen_asins) >= 15:
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
  ```

- [x] Verify: Run `python -c "from src.scraper.amazon_scraper import AmazonProductScraper; print('Import OK')"` — should succeed
- [x] Verify: Syntax check — `python -m py_compile src/scraper/utils.py && python -m py_compile src/scraper/base.py && python -m py_compile src/scraper/amazon_scraper.py`

STOP AND COMMIT

---

### Step 3: Amazon India scraper — product reviews

**Files:** `src/scraper/review_scraper.py`

- [x] Create `src/scraper/review_scraper.py`
  ```python
  import logging
  import re
  from urllib.parse import urljoin

  from bs4 import BeautifulSoup

  from src.scraper.base import BaseScraper

  logger = logging.getLogger(__name__)

  BASE_URL = "https://www.amazon.in"


  class AmazonReviewScraper(BaseScraper):
      def __init__(self, api_key: str | None = None, requests_per_minute: int = 30, max_pages: int = 5):
          super().__init__(api_key, requests_per_minute)
          self.max_pages = max_pages

      def _build_review_url(self, asin: str, page: int = 1) -> str:
          return f"{BASE_URL}/product-reviews/{asin}?reviewerType=all_reviews&pageNumber={page}"

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

      def scrape_product_reviews(self, asin: str, brand: str, max_reviews: int = 50) -> list[dict]:
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

      def scrape(self, products: list[dict], reviews_per_product: int = 50) -> list[dict]:
          all_reviews = []
          for product in products:
              asin = product["asin"]
              brand = product.get("brand", "Unknown")
              reviews = self.scrape_product_reviews(asin, brand, reviews_per_product)
              all_reviews.extend(reviews)

          self.save_raw(all_reviews, "reviews_raw.json")
          return all_reviews
  ```

- [x] Verify: `python -m py_compile src/scraper/review_scraper.py`

STOP AND COMMIT

---

### Step 4: Data cleaning and structuring

**Files:** `src/analysis/clean_data.py`

- [ ] Create `src/analysis/clean_data.py`
  ```python
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
  ```

- [ ] Verify: `python -m py_compile src/analysis/clean_data.py`

STOP AND COMMIT

---

### Step 5: Sentiment analysis engine

**Files:** `src/analysis/sentiment.py`, `src/analysis/themes.py`

- [ ] Create `src/analysis/sentiment.py`
  ```python
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
                      response = self._call_groq(prompt)
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
  ```

- [ ] Create `src/analysis/themes.py`
  ```python
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
  ```

- [ ] Verify: `python -m py_compile src/analysis/sentiment.py && python -m py_compile src/analysis/themes.py`

STOP AND COMMIT

---

### Step 6: Competitive analysis module

**Files:** `src/analysis/competitive.py`

- [ ] Create `src/analysis/competitive.py`
  ```python
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
      matrix = matrix.join(sentiment_brand.set_index("brand"), how="left")
      matrix = matrix.join(price_band_dist, how="left")
      matrix = matrix.join(vfm_by_brand.set_index("brand"), how="left")
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
  ```

- [ ] Verify: `python -m py_compile src/analysis/competitive.py`

STOP AND COMMIT

---

### Step 7: Dashboard — Overview page and app shell

**Files:** `src/dashboard/components.py`, `src/dashboard/app.py`, `src/dashboard/pages/01_Overview.py`

- [ ] Create `src/dashboard/components.py`
  ```python
  import json
  from pathlib import Path

  import pandas as pd
  import streamlit as st

  PROJECT_ROOT = Path(__file__).resolve().parents[2]


  @st.cache_data(ttl=300)
  def load_products() -> pd.DataFrame:
      path = PROJECT_ROOT / "data" / "cleaned" / "products.csv"
      if not path.exists():
          return pd.DataFrame()
      return pd.read_csv(path)


  @st.cache_data(ttl=300)
  def load_reviews() -> pd.DataFrame:
      path = PROJECT_ROOT / "data" / "cleaned" / "reviews.csv"
      if not path.exists():
          return pd.DataFrame()
      return pd.read_csv(path)


  @st.cache_data(ttl=300)
  def load_brand_summary() -> pd.DataFrame:
      path = PROJECT_ROOT / "data" / "cleaned" / "brand_summary.csv"
      if not path.exists():
          return pd.DataFrame()
      return pd.read_csv(path)


  @st.cache_data(ttl=300)
  def load_sentiment() -> pd.DataFrame:
      path = PROJECT_ROOT / "data" / "outputs" / "sentiment_scores.csv"
      if not path.exists():
          return pd.DataFrame()
      return pd.read_csv(path)


  @st.cache_data(ttl=300)
  def load_themes() -> dict:
      path = PROJECT_ROOT / "data" / "outputs" / "themes.json"
      if not path.exists():
          return {}
      with open(path, "r") as f:
          return json.load(f)


  @st.cache_data(ttl=300)
  def load_competitive_matrix() -> pd.DataFrame:
      path = PROJECT_ROOT / "data" / "outputs" / "competitive_matrix.csv"
      if not path.exists():
          return pd.DataFrame()
      return pd.read_csv(path)


  @st.cache_data(ttl=300)
  def load_insights() -> dict:
      path = PROJECT_ROOT / "data" / "outputs" / "insights.json"
      if not path.exists():
          return {}
      with open(path, "r") as f:
          return json.load(f)


  def kpi_card(label: str, value: str, delta: str | None = None, help_text: str | None = None):
      col1, col2, col3 = st.columns([1, 2, 1])
      with col2:
          st.markdown(
              f"""
              <div style="
                  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  padding: 20px;
                  border-radius: 10px;
                  color: white;
                  text-align: center;
                  margin-bottom: 10px;
              ">
                  <div style="font-size: 14px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
                  <div style="font-size: 28px; font-weight: bold; margin-top: 5px;">{value}</div>
                  {f'<div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">{delta}</div>' if delta else ''}
              </div>
              """,
              unsafe_allow_html=True,
          )
      if help_text:
          st.caption(help_text)


  def style_metric_card(label: str, value, prefix: str = "", suffix: str = ""):
      st.metric(label=label, value=f"{prefix}{value}{suffix}")


  def get_brand_colors() -> dict:
      colors = {
          "Safari": "#FF6B6B",
          "Skybags": "#4ECDC4",
          "American Tourister": "#45B7D1",
          "VIP": "#96CEB4",
          "Aristocrat": "#FFEAA7",
          "Nasher Miles": "#DDA0DD",
      }
      products = load_products()
      for brand in products["brand"].unique():
          if brand not in colors:
              import hashlib
              hash_val = int(hashlib.md5(brand.encode()).hexdigest()[:6], 16)
              colors[brand] = f"#{hash_val:06x}"
      return colors


  def no_data_message():
      st.warning("No data found. Please run the scraping and analysis pipeline first.")
      st.code("python -m src.scraper.amazon_scraper\npython -m src.scraper.review_scraper\npython -m src.analysis.clean_data\npython -m src.analysis.sentiment\npython -m src.analysis.themes\npython -m src.analysis.competitive")
  ```

- [ ] Create `src/dashboard/app.py`
  ```python
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
  ```

- [ ] Create `src/dashboard/pages/01_Overview.py`
  ```python
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

  import plotly.express as px
  import plotly.graph_objects as go
  import streamlit as st
  import pandas as pd

  from src.dashboard.components import (
      load_products,
      load_reviews,
      load_sentiment,
      load_brand_summary,
      no_data_message,
      get_brand_colors,
  )

  st.title("📊 Dashboard Overview")

  products_df = load_products()
  reviews_df = load_reviews()
  sentiment_df = load_sentiment()
  brand_summary_df = load_brand_summary()

  if products_df.empty or reviews_df.empty:
      no_data_message()
      st.stop()

  colors = get_brand_colors()
  brand_list = sorted(products_df["brand"].unique())

  st.markdown("---")

  col1, col2, col3, col4, col5 = st.columns(5)
  with col1:
      st.metric("Brands Tracked", len(brand_list))
  with col2:
      st.metric("Products Analyzed", len(products_df))
  with col3:
      st.metric("Reviews Analyzed", len(reviews_df))
  with col4:
      avg_sentiment = sentiment_df["sentiment_score"].mean() if not sentiment_df.empty else 0
      st.metric("Avg Sentiment", f"{avg_sentiment:.2f}", delta=None)
  with col5:
      avg_price = products_df["price"].mean()
      avg_discount = products_df["discount_pct"].mean()
      st.metric("Avg Discount", f"{avg_discount:.1f}%", delta=f"Avg price: ₹{avg_price:,.0f}")

  st.markdown("---")

  col_left, col_right = st.columns(2)

  with col_left:
      st.subheader("Products per Brand")
      product_counts = products_df.groupby("brand").size().reset_index(name="count")
      product_counts = product_counts.sort_values("count", ascending=True)
      fig_products = px.bar(
          product_counts,
          x="count",
          y="brand",
          orientation="h",
          color="brand",
          color_discrete_map=colors,
      )
      fig_products.update_layout(showlegend=False, height=350)
      st.plotly_chart(fig_products, use_container_width=True)

  with col_right:
      st.subheader("Reviews per Brand")
      review_counts = reviews_df.groupby("brand").size().reset_index(name="count")
      review_counts = review_counts.sort_values("count", ascending=True)
      fig_reviews = px.bar(
          review_counts,
          x="count",
          y="brand",
          orientation="h",
          color="brand",
          color_discrete_map=colors,
      )
      fig_reviews.update_layout(showlegend=False, height=350)
      st.plotly_chart(fig_reviews, use_container_width=True)

  st.markdown("---")

  col_left2, col_right2 = st.columns(2)

  with col_left2:
      st.subheader("Sentiment Distribution")
      if not sentiment_df.empty:
          fig_sentiment = px.histogram(
              sentiment_df,
              x="sentiment_score",
              nbins=30,
              color="brand",
              color_discrete_map=colors,
              labels={"sentiment_score": "Sentiment Score"},
          )
          fig_sentiment.update_layout(height=350)
          st.plotly_chart(fig_sentiment, use_container_width=True)

  with col_right2:
      st.subheader("Price vs Rating")
      fig_scatter = px.scatter(
          products_df,
          x="price",
          y="rating",
          color="brand",
          size="review_count",
          hover_name="title",
          color_discrete_map=colors,
          labels={"price": "Price (₹)", "rating": "Rating"},
      )
      fig_scatter.update_layout(height=350)
      st.plotly_chart(fig_scatter, use_container_width=True)

  st.markdown("---")

  st.subheader("Pricing Overview")
  if not brand_summary_df.empty and "avg_price" in brand_summary_df.columns:
      price_data = brand_summary_df.sort_values("avg_price")
      fig_pricing = go.Figure()
      fig_pricing.add_trace(go.Bar(
          name="Avg Price",
          x=price_data["brand_name"],
          y=price_data["avg_price"],
          marker_color="#667eea",
      ))
      fig_pricing.add_trace(go.Bar(
          name="Avg MRP",
          x=price_data["brand_name"],
          y=price_data["avg_mrp"],
          marker_color="#764ba2",
          opacity=0.4,
      ))
      fig_pricing.update_layout(barmode="group", height=400, title="Average Selling Price vs MRP")
      st.plotly_chart(fig_pricing, use_container_width=True)
  ```

- [ ] Verify: `python -m py_compile src/dashboard/components.py && python -m py_compile src/dashboard/app.py && python -m py_compile src/dashboard/pages/01_Overview.py`

STOP AND COMMIT

---

### Step 8: Dashboard — Brand Comparison view

**Files:** `src/dashboard/pages/02_Brand_Comparison.py`

- [ ] Create `src/dashboard/pages/02_Brand_Comparison.py`
  ```python
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

  import plotly.express as px
  import plotly.graph_objects as go
  import streamlit as st
  import pandas as pd

  from src.dashboard.components import (
      load_products,
      load_reviews,
      load_sentiment,
      load_brand_summary,
      load_competitive_matrix,
      load_themes,
      no_data_message,
      get_brand_colors,
  )

  st.title("⚖️ Brand Comparison")

  products_df = load_products()
  reviews_df = load_reviews()
  sentiment_df = load_sentiment()
  themes = load_themes()
  brand_summary_df = load_brand_summary()

  if products_df.empty:
      no_data_message()
      st.stop()

  colors = get_brand_colors()
  all_brands = sorted(products_df["brand"].unique())

  st.sidebar.subheader("Filters")
  selected_brands = st.sidebar.multiselect("Select Brands", all_brands, default=all_brands)
  min_rating = st.sidebar.slider("Minimum Rating", 0.0, 5.0, 0.0, 0.5)
  price_range = st.sidebar.slider(
      "Price Range (₹)",
      int(products_df["price"].min()),
      int(products_df["price"].max()),
      (int(products_df["price"].min()), int(products_df["price"].max())),
  )

  filtered_products = products_df[
      (products_df["brand"].isin(selected_brands))
      & (products_df["rating"] >= min_rating)
      & (products_df["price"].between(price_range[0], price_range[1]))
  ]

  filtered_sentiment = sentiment_df[sentiment_df["brand"].isin(selected_brands)] if not sentiment_df.empty else sentiment_df

  st.subheader("Side-by-Side Comparison")

  if not brand_summary_df.empty:
      comparison_df = brand_summary_df[brand_summary_df["brand_name"].isin(selected_brands)].copy()
      display_cols = [c for c in ["brand_name", "product_count", "avg_price", "avg_discount", "avg_rating", "total_reviews"] if c in comparison_df.columns]
      if "avg_sentiment" in comparison_df.columns:
          display_cols.append("avg_sentiment")
      st.dataframe(
          comparison_df[display_cols].sort_values("brand_name"),
          use_container_width=True,
          hide_index=True,
      )

  st.markdown("---")

  col_radar, col_bands = st.columns(2)

  with col_radar:
      st.subheader("Brand Radar Chart")
      if not brand_summary_df.empty and len(selected_brands) >= 2:
          radar_data = brand_summary_df[brand_summary_df["brand_name"].isin(selected_brands)].copy()

          radar_categories = []
          for col in ["avg_rating", "avg_discount", "avg_sentiment", "total_reviews"]:
              if col in radar_data.columns:
                  radar_categories.append(col)

          if radar_categories:
              radar_df = radar_data[["brand_name"] + radar_categories].copy()
              for col in radar_categories:
                  min_val = radar_df[col].min()
                  max_val = radar_df[col].max()
                  if max_val > min_val:
                      radar_df[col] = ((radar_df[col] - min_val) / (max_val - min_val)) * 100
                  else:
                      radar_df[col] = 50

              fig_radar = go.Figure()
              for _, row in radar_df.iterrows():
                  fig_radar.add_trace(go.Scatterpolar(
                      r=[row[c] for c in radar_categories] + [row[radar_categories[0]]],
                      theta=radar_categories + [radar_categories[0]],
                      fill="toself",
                      name=row["brand_name"],
                  ))
              fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=400)
              st.plotly_chart(fig_radar, use_container_width=True)
      else:
          st.info("Select at least 2 brands for radar chart")

  with col_bands:
      st.subheader("Price Band Distribution")
      if "price_band" not in filtered_products.columns:
          def compute_price_bands(price):
              if price <= 2000: return "Value"
              elif price <= 5000: return "Mid-Range"
              elif price <= 10000: return "Premium"
              else: return "Luxury"
          filtered_products = filtered_products.copy()
          filtered_products["price_band"] = filtered_products["price"].apply(compute_price_bands)

      band_counts = filtered_products.groupby(["brand", "price_band"]).size().reset_index(name="count")
      band_order = ["Value", "Mid-Range", "Premium", "Luxury"]
      band_counts["price_band"] = pd.Categorical(band_counts["price_band"], categories=band_order, ordered=True)

      fig_bands = px.bar(
          band_counts,
          x="brand",
          y="count",
          color="price_band",
          title="Products by Price Band",
          color_discrete_map={"Value": "#4ECDC4", "Mid-Range": "#667eea", "Premium": "#764ba2", "Luxury": "#FF6B6B"},
      )
      fig_bands.update_layout(height=400)
      st.plotly_chart(fig_bands, use_container_width=True)

  st.markdown("---")

  st.subheader("Top Pros & Cons by Brand")

  pros_cons_cols = st.columns(len(selected_brands))
  for i, brand in enumerate(selected_brands):
      with pros_cons_cols[i]:
          st.markdown(f"**{brand}**")
          brand_themes = themes.get(brand, {})
          if brand_themes:
              pros = brand_themes.get("top_pros", [])[:3]
              cons = brand_themes.get("top_cons", [])[:3]
              if pros:
                  st.markdown("🟢 **Pros:**")
                  for p in pros:
                      st.markdown(f"- {p.get('theme', str(p))}")
              if cons:
                  st.markdown("🔴 **Cons:**")
                  for c in cons:
                      st.markdown(f"- {c.get('theme', str(c))}")
          else:
              st.info("No theme data")

  st.markdown("---")

  if st.button("📥 Download Filtered Data as CSV"):
      csv = filtered_products.to_csv(index=False)
      st.download_button("Download", csv, "brand_comparison.csv", "text/csv")
  ```

- [ ] Verify: `python -m py_compile src/dashboard/pages/02_Brand_Comparison.py`

STOP AND COMMIT

---

### Step 9: Dashboard — Product Drilldown view

**Files:** `src/dashboard/pages/03_Product_Drilldown.py`

- [ ] Create `src/dashboard/pages/03_Product_Drilldown.py`
  ```python
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

  import plotly.express as px
  import streamlit as st
  import pandas as pd

  from src.dashboard.components import (
      load_products,
      load_reviews,
      load_sentiment,
      load_themes,
      no_data_message,
      get_brand_colors,
  )

  st.title("🔍 Product Drilldown")

  products_df = load_products()
  reviews_df = load_reviews()
  sentiment_df = load_sentiment()
  themes_dict = load_themes()

  if products_df.empty:
      no_data_message()
      st.stop()

  all_brands = sorted(products_df["brand"].unique())

  st.sidebar.subheader("Select Product")

  selected_brand = st.sidebar.selectbox("Brand", all_brands)

  brand_products = products_df[products_df["brand"] == selected_brand]["title"].tolist()

  if not brand_products:
      st.warning("No products found for this brand")
      st.stop()

  product_options = {f"{i+1}. {p[:80]}{'...' if len(p) > 80 else ''}": i for i, p in enumerate(brand_products)} if len(brand_products) > 15 else {p: i for i, p in enumerate(brand_products)}

  selected_product_title = st.sidebar.selectbox("Product", list(product_options.keys()))
  selected_idx = product_options[selected_product_title]
  product = products_df[products_df["brand"] == selected_brand].iloc[selected_idx]

  asin = product["asin"]

  st.markdown("### Product Details")

  col1, col2, col3, col4 = st.columns(4)
  with col1:
      st.metric("Price", f"₹{product['price']:,.0f}")
  with col2:
      st.metric("MRP", f"₹{product.get('mrp', product['price']):,.0f}")
  with col3:
      st.metric("Discount", f"{product.get('discount_pct', 0):.1f}%")
  with col4:
      st.metric("Rating", f"{product.get('rating', 'N/A')} ⭐")

  col5, col6, col7 = st.columns(3)
  with col5:
      st.metric("Reviews", f"{int(product.get('review_count', 0)):,}")
  with col6:
      st.metric("Brand", product["brand"])
  with col7:
      if product.get("url"):
          st.markdown(f"[View on Amazon]({product['url']})")

  st.markdown(f"**{product['title']}**")

  st.markdown("---")

  product_sentiment = sentiment_df[sentiment_df["asin"] == asin] if not sentiment_df.empty else pd.DataFrame()

  col_sent, col_aspects = st.columns(2)

  with col_sent:
      st.subheader("Review Sentiment")
      if not product_sentiment.empty:
          avg_sent = product_sentiment["sentiment_score"].mean()
          sentiment_label = "Positive" if avg_sent > 0.2 else "Negative" if avg_sent < -0.2 else "Neutral"
          sentiment_color = "🟢" if avg_sent > 0.2 else "🔴" if avg_sent < -0.2 else "🟡"

          st.metric("Average Sentiment", f"{avg_sent:.2f}", delta=sentiment_label)
          st.metric("Total Reviews Analyzed", len(product_sentiment))

          fig_hist = px.histogram(
              product_sentiment,
              x="sentiment_score",
              nbins=20,
              title="Sentiment Distribution",
              labels={"sentiment_score": "Sentiment Score"},
          )
          st.plotly_chart(fig_hist, use_container_width=True)
      else:
          st.info("No sentiment data for this product")

  with col_aspects:
      st.subheader("Aspect-Level Sentiment")
      if not product_sentiment.empty:
          aspect_cols = [c for c in product_sentiment.columns if c.startswith("aspect_")]
          if aspect_cols:
              aspect_data = []
              for col in aspect_cols:
                  counts = product_sentiment[col].value_counts()
                  aspect_name = col.replace("aspect_", "")
                  aspect_data.append({
                      "aspect": aspect_name,
                      "positive": counts.get("positive", 0),
                      "negative": counts.get("negative", 0),
                      "neutral": counts.get("neutral", 0),
                  })
              aspect_df = pd.DataFrame(aspect_data)
              fig_aspects = px.bar(
                  aspect_df,
                  x="aspect",
                  y=["positive", "negative", "neutral"],
                  title="Aspect Sentiment Breakdown",
                  barmode="stack",
                  color_discrete_map={"positive": "#4ECDC4", "negative": "#FF6B6B", "neutral": "#CCCCCC"},
              )
              st.plotly_chart(fig_aspects, use_container_width=True)
          else:
              st.info("No aspect data available")
      else:
          st.info("No sentiment data for this product")

  st.markdown("---")

  st.subheader("Top Appreciation & Complaint Themes")

  brand_themes = themes_dict.get(product["brand"], {})
  col_pros, col_cons = st.columns(2)

  with col_pros:
      st.markdown("🟢 **Top Appreciation**")
      pros = brand_themes.get("top_pros", [])[:5]
      for p in pros:
          theme = p.get("theme", str(p)) if isinstance(p, dict) else str(p)
          freq = p.get("frequency", "") if isinstance(p, dict) else ""
          st.markdown(f"- {theme}" + (f" ({freq})" if freq else ""))

  with col_cons:
      st.markdown("🔴 **Top Complaints**")
      cons = brand_themes.get("top_cons", [])[:5]
      for c in cons:
          theme = c.get("theme", str(c)) if isinstance(c, dict) else str(c)
          freq = c.get("frequency", "") if isinstance(c, dict) else ""
          st.markdown(f"- {theme}" + (f" ({freq})" if freq else ""))

  st.markdown("---")

  st.subheader("Review Rating Timeline")

  product_reviews = reviews_df[reviews_df["asin"] == asin] if not reviews_df.empty else pd.DataFrame()

  if not product_reviews.empty and "date" in product_reviews.columns:
      product_reviews_copy = product_reviews.copy()
      product_reviews_copy["date"] = pd.to_datetime(product_reviews_copy["date"], errors="coerce")
      product_reviews_copy = product_reviews_copy.dropna(subset=["date"])
      if not product_reviews_copy.empty:
          timeline = product_reviews_copy.groupby(product_reviews_copy["date"].dt.to_period("M")).agg(
              avg_rating=("rating", "mean"),
              count=("review_id", "count"),
          ).reset_index()
          timeline["date"] = timeline["date"].astype(str)

          fig_timeline = px.line(
              timeline,
              x="date",
              y="avg_rating",
              markers=True,
              title="Average Rating Over Time",
              labels={"date": "Month", "avg_rating": "Average Rating"},
          )
          fig_timeline.update_yaxes(range=[0, 5.5])
          st.plotly_chart(fig_timeline, use_container_width=True)
      else:
          st.info("No date data available for timeline")
  else:
      st.info("No review timeline data available")

  if st.button("📥 Download Product Reviews as CSV"):
      if not product_reviews.empty:
          csv = product_reviews.to_csv(index=False)
          st.download_button("Download Reviews", csv, f"reviews_{asin}.csv", "text/csv")
  ```

- [ ] Verify: `python -m py_compile src/dashboard/pages/03_Product_Drilldown.py`

STOP AND COMMIT

---

### Step 10: Dashboard — Agent Insights view

**Files:** `src/analysis/insights_generator.py`, `src/dashboard/pages/04_Agent_Insights.py`

- [ ] Create `src/analysis/insights_generator.py`
  ```python
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
  ```

- [ ] Create `src/dashboard/pages/04_Agent_Insights.py`
  ```python
  import sys
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

  import plotly.express as px
  import streamlit as st
  import pandas as pd

  from src.dashboard.components import (
      load_products,
      load_competitive_matrix,
      load_insights,
      no_data_message,
  )

  st.title("🤖 Agent Insights")

  products_df = load_products()
  insights_data = load_insights()

  if products_df.empty:
      no_data_message()
      st.stop()

  st.markdown("### AI-Generated Competitive Intelligence Insights")
  st.markdown("---")

  if st.button("🔄 Regenerate Insights", type="primary"):
      from src.analysis.insights_generator import InsightsGenerator
      with st.spinner("Generating insights with Llama 70B..."):
          try:
              generator = InsightsGenerator()
              insights_list = generator.generate_insights()
              insights_data = load_insights()
              st.success("Insights regenerated!")
          except Exception as e:
              st.error(f"Failed to generate insights: {e}")
              st.stop()

  agent_insights = insights_data.get("agent_insights", [])

  if not agent_insights:
      st.info("No insights generated yet. Click 'Regenerate Insights' to generate.")
      st.stop()

  category_icons = {
      "pricing": "💰",
      "quality": "⭐",
      "positioning": "🎯",
      "opportunity": "🚀",
      "risk": "⚠️",
  }
  category_colors = {
      "pricing": "#667eea",
      "quality": "#4ECDC4",
      "positioning": "#45B7D1",
      "opportunity": "#96CEB4",
      "risk": "#FF6B6B",
  }

  for i, insight in enumerate(agent_insights[:5]):
      if isinstance(insight, str):
          insight = {"insight": insight, "evidence": "", "implication": "", "category": "opportunity"}

      category = insight.get("category", "opportunity")
      icon = category_icons.get(category, "💡")
      color = category_colors.get(category, "#764ba2")

      with st.container():
          st.markdown(
              f"""
              <div style="
                  background: linear-gradient(135deg, {color}22 0%, {color}11 100%);
                  border-left: 4px solid {color};
                  padding: 20px;
                  border-radius: 8px;
                  margin-bottom: 15px;
              ">
                  <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">
                      {icon} Insight #{i+1}: {insight.get('category', '').title()}
                  </div>
                  <div style="font-size: 16px; margin-bottom: 10px;">
                      {insight.get('insight', '')}
                  </div>
                  <div style="font-size: 13px; color: #666; margin-bottom: 5px;">
                      📊 <strong>Evidence:</strong> {insight.get('evidence', '')}
                  </div>
                  <div style="font-size: 13px; color: #444;">
                      💡 <strong>Implication:</strong> {insight.get('implication', '')}
                  </div>
              </div>
              """,
              unsafe_allow_html=True,
          )

  st.markdown("---")

  st.subheader("Anomalies Detected")

  anomalies = insights_data.get("anomalies", [])
  if anomalies:
      for anomaly in anomalies:
          anomaly_type = anomaly.get("type", "unknown").replace("_", " ").title()
          st.warning(f"**{anomaly_type}**: {anomaly.get('description', anomaly)}")
  else:
      st.info("No anomalies detected in the current dataset.")

  st.markdown("---")

  st.subheader("Value for Money Rankings")

  competitive_matrix = load_competitive_matrix()
  if not competitive_matrix.empty and "avg_value_for_money" in competitive_matrix.columns:
      ranked = competitive_matrix.sort_values("avg_value_for_money", ascending=False)
      fig_vfm = px.bar(
          ranked,
          x="avg_value_for_money",
          y="brand",
          orientation="h",
          title="Value for Money Score (Sentiment adjusted by Price)",
          color="avg_value_for_money",
          color_continuous_scale="RdYlGn",
      )
      st.plotly_chart(fig_vfm, use_container_width=True)
  else:
      st.info("Value for money data not available. Run the competitive analysis pipeline.")

  if st.button("📥 Download Insights as JSON"):
      import json
      json_str = json.dumps(insights_data, ensure_ascii=False, indent=2)
      st.download_button("Download", json_str, "insights.json", "application/json")
  ```

- [ ] Verify: `python -m py_compile src/analysis/insights_generator.py && python -m py_compile src/dashboard/pages/04_Agent_Insights.py`

STOP AND COMMIT

---

### Step 11: Dashboard polish and interactions

**Files:** `src/dashboard/styles.css`, update `src/dashboard/app.py`, update `src/dashboard/components.py`

- [ ] Create `src/dashboard/styles.css`
  ```css
  .stApp {
      max-width: 1400px;
  }

  section[data-testid="stSidebar"] {
      background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  }

  section[data-testid="stSidebar"] .stMarkdown,
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] .stSelectbox label {
      color: #e0e0e0 !important;
  }

  h1, h2, h3 {
      color: #1a1a2e !important;
  }

  .stMetric {
      background: white;
      border-radius: 8px;
      padding: 10px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }

  .stMetric label {
      font-size: 13px !important;
      text-transform: uppercase;
      letter-spacing: 0.5px;
  }

  .stMetric .stMetricValue {
      font-size: 24px !important;
  }

  .stDataFrame {
      border-radius: 8px;
      overflow: hidden;
  }

  button[kind="primary"] {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  }

  .stAlert {
      border-radius: 8px;
  }

  .element-container:has(.stPlotlyChart) {
      padding: 5px 0;
  }

  @media (max-width: 768px) {
      .stApp {
          max-width: 100%;
      }
  }
  ```

- [ ] Update `src/dashboard/app.py` to include styles and caching
  ```python
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

  styles_path = Path(__file__).resolve().parent / "styles.css"
  if styles_path.exists():
      with open(styles_path) as f:
          st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

  overview = st.Page("pages/01_Overview.py", title="Overview", icon="📊")
  comparison = st.Page("pages/02_Brand_Comparison.py", title="Brand Comparison", icon="⚖️")
  drilldown = st.Page("pages/03_Product_Drilldown.py", title="Product Drilldown", icon="🔍")
  insights = st.Page("pages/04_Agent_Insights.py", title="Agent Insights", icon="🤖")

  pg = st.navigation([overview, comparison, drilldown, insights])
  pg.run()
  ```

- [ ] Add export functionality to `src/dashboard/components.py` — add this function at the end of the file:
  ```python
  def download_csv_button(df: pd.DataFrame, filename: str, button_label: str = "📥 Download CSV"):
      csv = df.to_csv(index=False)
      st.download_button(label=button_label, data=csv, file_name=filename, mime="text/csv")
  ```

- [ ] Verify: `python -m py_compile src/dashboard/app.py && python -m py_compile src/dashboard/components.py`
- [ ] Verify: Launch dashboard with `streamlit run src/dashboard/app.py` — should show sidebar navigation with 4 pages (data will be empty)
- [ ] Verify: No console errors, all pages load without crash

STOP AND COMMIT

---

### Step 12: Documentation and final deliverables

**Files:** `README.md`, `data/README.md`, `docs/architecture.md`, `docs/limitations.md`

- [ ] Create `README.md`
  ```markdown
  # 🧳 Luggage Brand Intelligence Dashboard

  Competitive intelligence dashboard for luggage brands on Amazon India. Scrapes pricing and review data, analyzes sentiment and themes, and surfaces actionable insights.

  ## Setup

  1. Clone the repo and create a virtual environment:
     ```bash
     python -m venv .venv
     source .venv/bin/activate  # or .venv\Scripts\activate on Windows
     pip install -r requirements.txt
     ```

  2. Copy `.env.example` to `.env` and add your API keys:
     ```
     SCRAPER_API_KEY=your_scraperapi_key
     GROQ_API_KEY=your_groq_api_key
     ```

  ## Pipeline

  Run each step in order:

  ```bash
  # 1. Scrape product listings
  python -m src.scraper.amazon_scraper

  # 2. Scrape product reviews
  python -m src.scraper.review_scraper

  # 3. Clean and structure data
  python -m src.analysis.clean_data

  # 4. Run sentiment analysis (requires GROQ_API_KEY)
  python -m src.analysis.sentiment

  # 5. Extract themes
  python -m src.analysis.themes

  # 6. Build competitive analysis
  python -m src.analysis.competitive

  # 7. Generate agent insights
  python -m src.analysis.insights_generator
  ```

  ## Dashboard

  ```bash
  streamlit run src/dashboard/app.py
  ```

  ## Project Structure

  ```
  src/
  ├── scraper/          # Amazon India scrapers
  │   ├── base.py       # Base scraper class
  │   ├── amazon_scraper.py  # Product listing scraper
  │   ├── review_scraper.py  # Review scraper
  │   └── utils.py            # HTTP utils, rate limiting
  ├── analysis/         # Data analysis modules
  │   ├── clean_data.py       # Data cleaning pipeline
  │   ├── sentiment.py        # Sentiment analysis (Groq/Llama)
  │   ├── themes.py           # Theme extraction
  │   ├── competitive.py      # Competitive analysis
  │   └── insights_generator.py # AI insight generation
  └── dashboard/        # Streamlit dashboard
      ├── app.py               # Main app entry
      ├── components.py        # Shared components & data loading
      ├── styles.css           # Custom styling
      └── pages/               # Dashboard pages
  ```

  ## Data Scope

  | Metric          | Value                                    |
  |-----------------|------------------------------------------|
  | Brands          | Safari, Skybags, American Tourister, VIP, Aristocrat, Nasher Miles |
  | Products/brand  | 10+                                      |
  | Reviews/brand   | 50+                                      |

  ## Tech Stack

  - **Scraping:** requests + ScraperAPI + BeautifulSoup4
  - **Data:** Pandas
  - **Sentiment:** Groq API (Llama 70B)
  - **Dashboard:** Streamlit + Plotly
  - **Config:** PyYAML + python-dotenv

  ## Sentiment Methodology

  Reviews are analyzed using Llama 3.3 70B via Groq API. Each review receives:
  - A sentiment score from -1.0 (very negative) to 1.0 (very positive)
  - Aspect-level tags for wheels, handle, zipper, material, size, and durability
  - Key sentiment phrases

  Theme extraction aggregates per-brand insights including top pros/cons and overall sentiment summary.

  ## Limitations

  See [docs/limitations.md](docs/limitations.md) for details.
  ```

- [ ] Create `data/README.md`
  ```markdown
  # Data Directory

  ## Structure

  - `raw/` — Raw scraped data (products_raw.json, reviews_raw.json)
  - `cleaned/` — Cleaned datasets (products.csv, reviews.csv, brand_summary.csv)
  - `outputs/` — Analysis outputs (sentiment_scores.csv, themes.json, competitive_matrix.csv, insights.json)

  ## Schema

  ### products.csv

  | Column        | Type    | Description                         |
  |---------------|---------|-------------------------------------|
  | asin          | string  | Amazon product ID                   |
  | brand         | string  | Brand name                          |
  | title         | string  | Product title                       |
  | url           | string  | Amazon product URL                  |
  | price         | float   | Selling price in INR                |
  | mrp           | float   | Maximum retail price in INR         |
  | discount_pct  | float   | Discount percentage                 |
  | rating        | float   | Average star rating (1-5)           |
  | review_count  | int     | Number of reviews                   |
  | image_url     | string  | Product image URL                   |
  | availability  | string  | Availability status                 |

  ### reviews.csv

  | Column            | Type    | Description                              |
  |-------------------|---------|------------------------------------------|
  | review_id         | string  | Review identifier                        |
  | asin              | string  | Product ASIN                             |
  | brand             | string  | Brand name                               |
  | title             | string  | Review title                             |
  | body              | string  | Review body text                         |
  | rating            | int     | Star rating (1-5)                        |
  | date              | string  | Review date                              |
  | verified_purchase | bool    | Verified purchase flag                   |
  | helpful_votes     | int     | Helpful vote count                      |

  ### sentiment_scores.csv

  | Column           | Type   | Description                                    |
  |------------------|--------|------------------------------------------------|
  | review_id        | string | Review identifier                              |
  | asin             | string | Product ASIN                                   |
  | brand            | string | Brand name                                    |
  | sentiment_score  | float  | Sentiment score (-1.0 to 1.0)                 |
  | aspect_*         | string | Aspect-level sentiment (positive/negative/neutral) |
  | key_phrases      | string | Pipe-separated key sentiment phrases           |

  ## Scraping Limitations

  - Data sourced from Amazon India public listings
  - Review sample size may vary by product availability
  - Only English reviews are captured
  - ScraperAPI free tier: 1000 requests/month
  ```

- [ ] Create `docs/architecture.md`
  ```markdown
  # Architecture

  ## Data Flow

  ```
  Amazon.in ──► ScraperAPI ──► Raw HTML ──► BeautifulSoup ──► Structured JSON
                                                                      │
                                                                      ▼
  Dashboard ◄── Cleaned CSV ◄── Data Cleaning ◄── Raw JSON
      │                                                               │
      │                                                               ▼
      │                                                   Sentiment Analysis (Groq/Llama 70B)
      │                                                               │
      │                                                               ▼
      └────────────────────────────────────────────── Outputs (CSV, JSON)
   ```

  ## Components

  ### Scraper Layer
  - `AmazonProductScraper` — Searches brand listings, extracts product details
  - `AmazonReviewScraper` — Fetches and parses product reviews
  - `RateLimiter` — Throttles requests to stay within API limits
  - Uses ScraperAPI for anti-bot bypass (configurable, can fall back to direct requests)

  ### Analysis Layer
  - `clean_data.py` — Parses prices, fills missing values, creates brand summaries
  - `SentimentAnalyzer` — Batch sentiment scoring via Groq API with Llama 70B
  - `ThemeExtractor` — Brand-level pros/cons/summary extraction
  - `competitive.py` — Price bands, value-for-money, anomaly detection
  - `InsightsGenerator` — AI-generated competitive insights

  ### Dashboard Layer
  - Streamlit multi-page app with 4 views
  - Plotly interactive charts
  - CSV export, filters, and drilldowns
  - Responsive layout with custom CSS

  ## Key Design Decisions

  1. **ScraperAPI over Playwright**: Simpler setup, handles anti-bot measures, no browser dependency
  2. **Groq/Llama over local model**: Higher quality sentiment analysis, free tier sufficient for dataset size
  3. **CSV/JSON over database**: Simpler setup, portable, appropriate for dataset size
  4. **Streamlit over React**: Faster development, Python-native, sufficient for dashboard needs
  5. **Batch sentiment analysis**: Reduces API calls by grouping reviews
  ```

- [ ] Create `docs/limitations.md`
  ```markdown
  # Limitations and Future Improvements

  ## Current Limitations

  1. **Scraping reliability**: Amazon may change HTML structure, breaking parsers. ScraperAPI free tier has 1000 requests/month limit.
  2. **Review language**: Only English reviews are captured. Hindi and other regional language reviews are excluded.
  3. **Sample bias**: Reviews may skew toward very positive or very negative experiences.
  4. **Sentiment accuracy**: LLM-based sentiment analysis can hallucinate scores. Manual spot-checking is recommended.
  5. **Static dataset**: Data is not automatically refreshed. Re-scraping requires running the pipeline manually.
  6. **Price volatility**: Amazon prices change frequently. The captured prices are point-in-time snapshots.
  7. **Product categorization**: Search-based scraping may include non-luggage products in results.

  ## Future Improvements

  1. **Scheduled scraping**: Automate data collection on a daily/weekly basis
  2. **Database storage**: Move from CSV to SQLite or PostgreSQL for better querying
  3. **Real-time dashboard**: WebSocket-based updates for live monitoring
  4. **Trend analysis**: Track price and sentiment changes over time
  5. **Multi-marketplace**: Extend to Flipkart, Myntra, and other Indian marketplaces
  6. **Review deduplication**: Better handling of duplicate or incentivized reviews
  7. **Email alerts**: Notify when significant price changes or sentiment shifts occur
  8. **Aspect-level dashboard**: Separate views for each aspect category (durability, value, etc.)
  ```

- [ ] Verify: `README.md` setup instructions work end-to-end on a fresh clone
- [ ] Verify: All referenced files exist in the project structure
- [ ] Verify: `docs/` contains architecture.md and limitations.md

STOP AND COMMIT

---

### Step 13: Pipeline runner script (Bonus — single command to run everything)

**Files:** `run_pipeline.py`

- [ ] Create `run_pipeline.py` at project root
  ```python
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
          max_pages=config["scraping"]["max_review_pages"],
      )
      reviews = scraper.scrape(products, config["scraping"]["reviews_per_product"])
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
  ```

- [ ] Verify: `python -m py_compile run_pipeline.py`
- [ ] Verify: `python run_pipeline.py --help` shows usage

STOP AND COMMIT

---

## Verification Checklist

- [ ] `pip install -r requirements.txt` succeeds
- [ ] `python -m src.scraper.amazon_scraper` scrapes product data (requires API key)
- [ ] `python -m src.scraper.review_scraper` scrapes review data (requires API key)
- [ ] `python -m src.analysis.clean_data` produces cleaned CSVs
- [ ] `python -m src.analysis.sentiment` runs sentiment analysis (requires Groq key)
- [ ] `python -m src.analysis.themes` extracts themes (requires Groq key)
- [ ] `python -m src.analysis.competitive` builds competitive matrix
- [ ] `python -m src.analysis.insights_generator` generates insights (requires Groq key)
- [ ] `streamlit run src/dashboard/app.py` launches dashboard successfully
- [ ] All 4 dashboard pages render without errors
- [ ] Filters update visualizations dynamically
- [ ] Export CSV download works
- [ ] `python run_pipeline.py --all` runs end-to-end
- [ ] README instructions work on fresh clone

## Important Notes

1. **API Keys Required**: Both ScraperAPI and Groq API keys are needed for the full pipeline. The dashboard works with pre-scraped data without keys.
2. **Rate Limiting**: The scraper respects ScraperAPI free tier limits (1000 req/month). Adjust `requests_per_minute` in `config.yaml` as needed.
3. **Groq Free Tier**: Groq free tier has rate limits (30 req/min, 6000 tokens/min). The sentiment analysis batches reviews to stay within limits.
4. **Data Size**: With 6 brands × 10+ products × 50+ reviews, expect ~300-400 ScraperAPI calls and ~30-60 Groq API calls.
5. **Streamlit Version**: Requires Streamlit 1.36+ for `st.navigation()` and `st.Page()`.