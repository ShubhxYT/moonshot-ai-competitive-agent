# 🧳 Luggage Brand Intelligence Dashboard

Competitive intelligence dashboard for luggage brands on Amazon India. Scrapes pricing and review data, analyzes sentiment and themes, and surfaces actionable insights.

## Setup

1. Create a virtual environment and install dependencies:
   ```bash
   uv sync
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
