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
