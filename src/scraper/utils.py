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


def fetch_via_scraper_api(url: str, api_key: str, session: requests.Session = None, render: bool = False) -> str:
    if session is None:
        session = create_session()
    api_url = "http://api.scraperapi.com/"
    params = {"api_key": api_key, "url": url, "country_code": "in"}
    if render:
        params["render"] = "true"
    logger.info(f"Fetching via ScraperAPI: {url}")
    response = session.get(api_url, params=params, timeout=120)
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
