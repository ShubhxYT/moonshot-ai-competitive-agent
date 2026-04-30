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
