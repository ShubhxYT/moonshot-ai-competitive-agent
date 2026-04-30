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
