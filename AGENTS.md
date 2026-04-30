/# Munshot — Competitive Intelligence Dashboard

## What this is
Interactive Streamlit dashboard scraping/synthesizing Amazon India luggage reviews + pricing for 6 brands (Safari, Skybags, American Tourister, VIP, Aristocrat, Nasher Miles). Python project, planning stage (no src yet).

## Quick start
```bash
cp .env.example .env   # fill in SCRAPER_API_KEY + GROQ_API_KEY
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
# Then run each step in order (outputs feed downstream):
python -m src.scraper.amazon_scraper   # Step 2: product listings
python -m src.scraper.review_scraper   # Step 3: reviews
python -m src.analysis.clean_data      # Step 4: clean + aggregate
python -m src.analysis.sentiment       # Step 5a: LLM sentiment via Groq
python -m src.analysis.themes          # Step 5b: theme extraction
python -m src.analysis.competitive     # Step 6: competitive matrix + anomalies
streamlit run src/dashboard/app.py     # Step 7-11: launch dashboard
```

## Architecture
```
src/
  scraper/        # Amazon.in scraping (requests + ScraperAPI + BeautifulSoup)
  analysis/       # Cleaning, Groq-based sentiment/themes, competitive matrix
  dashboard/      # Streamlit multi-page app (Overview, Brand Comparison, Product Drilldown, Agent Insights)
data/
  raw/            # Raw scraped JSON (gitignored)
  cleaned/        # CSV/Parquet (gitignored)
  outputs/        # Sentiment scores, themes, competitive matrix (gitignored)
plans/            # Assignment doc + implementation plan
```

## Dependencies
- **ScraperAPI** (free tier: 1k req/mo) — anti-bot proxy for Amazon.in
- **Groq API** (`llama-3.3-70b-versatile`, free tier) — sentiment + theme extraction
- Req per brand: ~3 search pages + ~5 review pages/product x ~10 products = ~53 refills

## Key conventions
- **All data dirs gitignored** — data/raw/, cleaned/, outputs/
- **Env vars**: `SCRAPER_API_KEY`, `GROQ_API_KEY` (loaded via `dotenv` in dashboard only; scraper/analysis pass explicitly)
- **Rate limiting**: 30 req/min via `RateLimiter` in `utils.py`
- **Sentiment cache**: `data/outputs/sentiment_cache.json` — avoids re-Groq-ing same reviews
- **Streamlit**: multi-page via `st.Page` + `st.navigation`; `sys.path.insert(0, ...)` hack for imports
- **`config.yaml`** controls brands, scraping params, sentiment model name

## Gotchas
- No git repo yet — run `git init` before any commits
- `src/` is not a package (no `pyproject.toml` installed yet) — the dashboard uses `sys.path.insert` to find modules
- `ruff` config in `pyproject.toml`: line-length=120, select=E,F,I
- `clean_data.py` reads from `data/raw/` and writes to `data/cleaned/` — must run after scraping
- `sentiment.py` requires `GROQ_API_KEY` env var — will `raise ValueError` if missing
- Theme extraction depends on sentiment results already being in `data/outputs/sentiment_scores.csv`
- Anomaly detection threshold: >40% negative aspect reviews, >=4.0 rating with negative sentiment, >=40% discount with <3.5 stars

## Plans
`plans/competitive-intelligence-dashboard/plan.md` — full step-by-step spec, code samples, and verification checks per step. Consult before implementing any module.
