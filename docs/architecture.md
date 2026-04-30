# Architecture

## Data Flow

```
Amazon.in ──► ScraperAPI ──► Raw HTML ──► BeautifulSoup ──► Structured JSON
                                                                   │
                                                                   ▼
Dashboard ◄── Cleaned CSV ◄── Data Cleaning ◄── Raw JSON
    │                                                           │
    │                                                           ▼
    │                                                Sentiment Analysis (Groq/Llama 70B)
    │                                                           │
    │                                                           ▼
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
