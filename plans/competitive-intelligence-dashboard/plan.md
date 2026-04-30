# Competitive Intelligence Dashboard for Amazon India Luggage Brands

Branch: `main`

## Goal

Build an interactive dashboard that scrapes, analyzes, and visualizes pricing and review sentiment data for 4+ luggage brands on Amazon India, enabling competitive comparison and insight discovery.

## Architecture Overview

**Stack:** Python + Scraping API (free tier) + Pandas (data) + Streamlit (dashboard) + Plotly (charts) + Groq API with Llama 70B (sentiment/theme analysis)

**Data Flow:** Scrape via API → Clean → Analyze → Store (CSV/Parquet) → Dashboard

**External APIs:** Groq API (Llama 70B for sentiment + theme extraction), free scraping API service

## Steps

### Step 1: Project scaffolding and dependency setup

**Files:** `pyproject.toml`, `requirements.txt`, `.gitignore`, `README.md`, `src/`, `data/`, `config.yaml`

**What:**
- Initialize Python project with pyproject.toml
- Define dependencies: playwright, pandas, plotly, streamlit, beautifulsoup4, requests, pyyaml, transformers (or openai for LLM sentiment), python-dotenv
- Create directory structure: `src/scraper/`, `src/analysis/`, `src/dashboard/`, `data/raw/`, `data/cleaned/`, `data/outputs/`
- Add .gitignore for Python, data files, .env
- Create config.yaml for brands, products per brand, reviews per product, rate limits
- Write initial README with setup instructions and project overview

**Testing:** `pip install -r requirements.txt` succeeds, `playwright install` completes, project structure validates

---

### Step 2: Amazon India scraper — product listing

**Files:** `src/scraper/base.py`, `src/scraper/amazon_scraper.py`, `src/scraper/utils.py`, `data/raw/products_raw.json`

**What:**
- Build scraper using free scraping API service (e.g., ScraperAPI free tier, ScrapingBee free tier, or similar)
- Construct Amazon.in search URLs per brand (e.g., "Safari luggage", "American Tourister suitcase")
- Send requests through scraping API to bypass anti-bot measures
- Parse HTML response with BeautifulSoup
- Extract: product title, ASIN, URL, price, MRP, discount %, star rating, review count, image URL, availability
- Handle pagination via search result pages
- Implement rate limiting to stay within free tier limits
- Save raw data to `data/raw/products_raw.json`
- Log scraping progress, errors, and API usage

**Testing:** Run scraper for 1 brand, verify 10+ products captured with all fields populated, check data integrity

---

### Step 3: Amazon India scraper — product reviews

**Files:** `src/scraper/review_scraper.py`, `data/raw/reviews_raw.json`

**What:**
- For each product, construct Amazon.in review page URL
- Fetch review pages through scraping API
- Parse and extract: review title, body, rating, date, verified purchase flag, helpful votes
- Handle pagination through review pages
- Target 50+ reviews per brand minimum
- Filter to English reviews only
- Save to `data/raw/reviews_raw.json` linked by ASIN
- Implement deduplication and filtering (remove empty reviews)
- Track API usage to stay within free tier

**Testing:** Run review scraper for 2-3 products, verify 50+ reviews per brand, check field completeness and ASIN linkage

---

### Step 4: Data cleaning and structuring

**Files:** `src/analysis/clean_data.py`, `data/cleaned/products.csv`, `data/cleaned/reviews.csv`, `data/cleaned/brand_summary.csv`

**What:**
- Parse prices (remove ₹, commas), convert to float
- Calculate discount % from MRP and selling price
- Normalize ratings (handle "X out of 5" formats)
- Parse dates to datetime
- Merge products and reviews on ASIN
- Create brand_summary.csv with aggregated metrics per brand
- Handle missing values, outliers, duplicates
- Export clean datasets to CSV and Parquet

**Testing:** Validate no null critical fields, price ranges are reasonable, brand aggregations match raw data counts

---

### Step 5: Sentiment analysis engine

**Files:** `src/analysis/sentiment.py`, `src/analysis/themes.py`, `data/outputs/sentiment_scores.csv`, `data/outputs/themes.json`

**What:**
- Use Groq API with Llama 70B model for sentiment analysis
- Design prompt template to extract:
  - Sentiment score (-1 to +1) per review
  - Aspect-level tags (wheels, handle, zipper, material, size, durability)
  - Whether review is positive/negative for each aspect
- Batch reviews to stay within Groq free tier rate limits
- Aggregate sentiment by product and brand
- Extract recurring themes using LLM:
  - Top 5 pros and top 5 cons per brand
  - Summary of recurring praise and complaints
- Output sentiment_scores.csv and themes.json
- Cache LLM responses to avoid re-processing

**Testing:** Spot-check 20 reviews manually against model scores, verify theme extraction surfaces known luggage issues, check brand-level sentiment correlates with star ratings

---

### Step 6: Competitive analysis module

**Files:** `src/analysis/competitive.py`, `data/outputs/competitive_matrix.csv`, `data/outputs/insights.json`

**What:**
- Build brand comparison matrix: avg price, avg discount, avg rating, review count, sentiment score
- Calculate price bands (premium, mid-range, value)
- Compute value-for-money score (sentiment adjusted by price)
- Detect anomalies (e.g., high rating but durability complaints)
- Generate structured insights: who is winning, why, where gaps exist
- Output competitive_matrix.csv and insights.json for dashboard consumption

**Testing:** Verify comparison matrix numbers match cleaned data, check price band classifications are reasonable, validate anomaly detection logic

---

### Step 7: Dashboard — Overview page

**Files:** `src/dashboard/app.py`, `src/dashboard/pages/01_Overview.py`, `src/dashboard/components.py`

**What:**
- Set up Streamlit multi-page app
- Overview page with KPI cards:
  - Total brands tracked, products analyzed, reviews analyzed
  - Average sentiment snapshot across all brands
  - Pricing overview (price range, avg discount)
- Brand distribution charts (products per brand, reviews per brand)
- Sentiment distribution histogram
- Price vs rating scatter plot colored by brand

**Testing:** App launches successfully, all KPIs display correct numbers, charts render with proper data, responsive layout

---

### Step 8: Dashboard — Brand Comparison view

**Files:** `src/dashboard/pages/02_Brand_Comparison.py`

**What:**
- Side-by-side brand comparison table (sortable)
- Metrics: avg price, avg discount %, avg rating, review count, sentiment score
- Top pros and cons per brand (from theme analysis)
- Radar chart comparing brands across dimensions
- Price band visualization (stacked bar or treemap)
- Filter controls: brand selector, price range, min rating, sentiment filter

**Testing:** Table sorts correctly on all columns, filters update all visualizations dynamically, radar chart displays accurately, pros/cons match theme data

---

### Step 9: Dashboard — Product Drilldown view

**Files:** `src/dashboard/pages/03_Product_Drilldown.py`

**What:**
- Product selector (dropdown or searchable list)
- Product detail card: title, price, MRP, discount, rating, review count
- Review synthesis summary (LLM-generated or template-based)
- Top complaint themes and top appreciation themes for this product
- Review timeline (ratings over time)
- Link to Amazon product page

**Testing:** Product selection updates all details, themes match product-level data, timeline renders correctly, external link works

---

### Step 10: Dashboard — Agent Insights view (Bonus)

**Files:** `src/dashboard/pages/04_Agent_Insights.py`, `src/analysis/insights_generator.py`

**What:**
- Use Groq API with Llama 70B to auto-generate 5 non-obvious conclusions
- Feed competitive matrix and sentiment data as context to LLM
- Design prompt to produce actionable, data-backed insights
- Present insights as cards with supporting data points
- Examples: "Brand X wins on sentiment despite premium pricing because...", "Durability complaints for Brand Y are concentrated in products above ₹5000"
- Include value-for-money rankings (sentiment adjusted by price)
- Include anomaly highlights (high rating but specific complaints)
- Cache insights to avoid re-processing on each dashboard load

**Testing:** Insights are specific and data-backed (not generic), each insight references actual numbers, insights change when data changes

---

### Step 11: Dashboard — Polish and interactions

**Files:** `src/dashboard/app.py`, `src/dashboard/components.py`, `src/dashboard/styles.css`

**What:**
- Consistent styling across all pages (custom CSS theme)
- Add loading states and error boundaries
- Ensure all filters work across all views
- Add export functionality (download filtered data as CSV)
- Add tooltips and help text for metrics
- Optimize performance (cache data loading, use st.cache_data)
- Mobile-responsive layout where possible

**Testing:** All interactions work without page reload, filters persist across views, export produces correct data, no console errors, load time < 5 seconds

---

### Step 12: Documentation and final deliverables

**Files:** `README.md`, `data/README.md`, `docs/architecture.md`, `docs/limitations.md`

**What:**
- README: setup instructions, how to run scraper, how to launch dashboard, project structure
- Data README: dataset schema, scraping limitations, sample sizes per brand
- Architecture diagram (Mermaid or image)
- Sentiment methodology documentation
- Limitations and future improvements section
- Clean final dataset in `data/cleaned/` and `data/outputs/`
- Optional: record Loom walkthrough script outline

**Testing:** README instructions work end-to-end on fresh clone, all referenced files exist, architecture diagram matches implementation

---

## Dependencies

| Package | Purpose |
|---------|---------|
| requests | HTTP requests to scraping API |
| pandas | Data manipulation and analysis |
| streamlit | Dashboard framework |
| plotly | Interactive charts |
| beautifulsoup4 | HTML parsing from scraped content |
| groq | Groq API client for Llama 70B |
| pyyaml | Configuration management |
| python-dotenv | Environment variables (API keys) |

## Data Scope

| Metric | Target |
|--------|--------|
| Brands | 6 (Safari, Skybags, American Tourister, VIP, Aristocrat, Nasher Miles) |
| Products per brand | 10+ |
| Reviews per brand | 50+ |

## Decisions Made

1. **Sentiment approach**: Groq API with Llama 70B (free tier with rate limits). Provides high-quality sentiment + theme extraction.
2. **Scraping strategy**: Free scraping API service (e.g., ScraperAPI free tier, or similar). Handles anti-bot measures automatically.
3. **Deployment**: Local-only. Dashboard runs locally for submission.
4. **Review languages**: English only. No translation step needed.
