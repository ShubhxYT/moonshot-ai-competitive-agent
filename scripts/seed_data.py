"""
Generates realistic sample data for demo purposes and saves it to data/raw/.
Run this instead of the scrapers when you want a guaranteed working demo.

Usage:
    uv run python scripts/seed_data.py
"""
import json
import random
from pathlib import Path

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BRANDS = [
    {"name": "Safari", "asin_prefix": "B08SAF", "price_range": (2500, 8000), "rating_range": (3.8, 4.5)},
    {"name": "Skybags", "asin_prefix": "B07SKY", "price_range": (1800, 6500), "rating_range": (3.6, 4.4)},
    {"name": "American Tourister", "asin_prefix": "B09AMT", "price_range": (3500, 12000), "rating_range": (4.0, 4.7)},
    {"name": "VIP", "asin_prefix": "B06VIP", "price_range": (2000, 7500), "rating_range": (3.7, 4.3)},
    {"name": "Aristocrat", "asin_prefix": "B05ARI", "price_range": (1500, 5500), "rating_range": (3.5, 4.2)},
    {"name": "Nasher Miles", "asin_prefix": "B10NAS", "price_range": (2200, 9000), "rating_range": (3.9, 4.6)},
]

PRODUCT_TITLES = {
    "Safari": [
        "Safari Polycarbonate 75 cm Large Hard Luggage Trolley Bag (Black)",
        "Safari Thorium 67 cm Medium Hardsided Spinner Suitcase (Blue)",
        "Safari Shock Hard Luggage Trolley with Anti-Scratch Wheels (Red)",
        "Safari Cosmos 55 cm Cabin Hard Luggage (Grey)",
        "Safari Regloss 79 cm Extra Large Hardside Trolley (Teal)",
    ],
    "Skybags": [
        "Skybags Mint Polyester 67 cm Blue Softsided Trolley Bag",
        "Skybags Rubik Polycarbonate 77 cm Hard Luggage (Midnight Blue)",
        "Skybags Beetle Polypropylene Hardsided Cabin Bag (Black)",
        "Skybags Trooper Polyester 55 cm Cabin Trolley (Navy)",
        "Skybags Fiesta 79 cm Hardside Spinner (Magenta)",
    ],
    "American Tourister": [
        "American Tourister Linex Polycarbonate 69 cm Hard Luggage (Seaport Blue)",
        "American Tourister Ivy Polypropylene 79 cm Hard Luggage (Steel Blue)",
        "American Tourister Splash SP 55 cm Cabin Spinner (Black)",
        "American Tourister Jazz SP 68 cm Medium Hardside (Stone Blue)",
        "American Tourister Linex Spinner 55/20 TSA Cabin Bag (Coral Red)",
    ],
    "VIP": [
        "VIP Turbo Strolly 75 cm Large Trolley Bag (Black)",
        "VIP Maestro Polycarbonate Hard Cabin Luggage 55 cm (Red)",
        "VIP Fresco 65 cm 4 Wheel Spinner Luggage (Grey)",
        "VIP Contour Hard Trolley 77 cm Large (Navy Blue)",
        "VIP Alpha Hard Spinner 55 cm Cabin Luggage (Silver)",
    ],
    "Aristocrat": [
        "Aristocrat Matrix Polyester 67 cm Softsided Check-in Trolley (Black)",
        "Aristocrat Optima Hard 55 cm Cabin Luggage (Red)",
        "Aristocrat Glide Softside 79 cm Large Trolley Bag (Blue)",
        "Aristocrat Dazzle Hard 77 cm Spinner Luggage (Champagne)",
        "Aristocrat Nite Hard 55 cm Cabin Trolley (Magenta)",
    ],
    "Nasher Miles": [
        "Nasher Miles Bangalore Polycarbonate Check-in Luggage 65 cm (Blue)",
        "Nasher Miles Hard Luggage Trolley Spinner 55 cm Cabin (Black)",
        "Nasher Miles Dubai Polycarbonate 77 cm Hard Luggage (Grey)",
        "Nasher Miles Glasgow Hard Cabin Trolley 55 cm (Orange)",
        "Nasher Miles Amsterdam Polycarbonate 65 cm Spinner (Dusty Pink)",
    ],
}

REVIEW_POSITIVE_TITLES = [
    "Excellent product, very sturdy",
    "Great quality for the price",
    "Very happy with this purchase",
    "Smooth wheels, good build quality",
    "Exactly as described, love it",
    "Durable and lightweight",
    "Best suitcase I've bought",
    "Premium feel at affordable price",
]

REVIEW_NEGATIVE_TITLES = [
    "Zipper broke after 2 trips",
    "Wheels not smooth on rough roads",
    "Handle felt loose",
    "Disappointed with the quality",
    "Not worth the price",
]

REVIEW_NEUTRAL_TITLES = [
    "Decent product, nothing exceptional",
    "Okay for the price",
    "Meets basic requirements",
    "Average quality, expected more",
]

REVIEW_BODIES = {
    "positive": [
        "I bought this for my international trip and it performed flawlessly. The hard shell is very tough and the wheels glide perfectly on airport floors. The zipper is smooth and locks well with TSA lock. Highly recommend!",
        "This luggage exceeded my expectations. Lightweight yet very sturdy. Packed it fully and it survived checked-in handling without a scratch. The telescopic handle extends smoothly and locks at multiple heights.",
        "Amazing product! Used it on 3 domestic flights already. The spinner wheels are fantastic—rotates 360 degrees effortlessly. Interior is well-organized with a good divider and straps. Very satisfied.",
        "Great quality at this price point. The polycarbonate shell is scratch-resistant and the zipper feels premium. Love the color too. Will definitely buy again.",
        "Bought this as a replacement for my old bag. The difference is night and day. Build quality is solid, handle does not wobble, wheels are smooth. Interior has enough space for a week-long trip.",
        "Excellent luggage! The hard shell protected all my fragile items perfectly. TSA lock works great. Wheels are quiet and smooth even on uneven surfaces. Very happy with the purchase.",
    ],
    "negative": [
        "Disappointed with the quality. The zipper started showing wear after just 2 trips. Expected better build quality for this price. The wheels also make a rattling noise on smooth surfaces.",
        "The handle is flimsy and wobbles even when extended halfway. Not ideal for someone with a lot of walking. The material also scuffs very easily despite being marketed as scratch-resistant.",
        "Wheels broke on the second trip. One wheel stopped spinning freely which made it impossible to roll properly. Customer service was unhelpful. Would not recommend.",
        "The locking mechanism on the zipper is unreliable. After the first wash of the interior lining, the zipper pull came off. Overall build quality feels cheap for the price.",
        "Not worth the money. The hard shell cracked on the corner after mild handling. TSA lock is also very stiff and hard to reset. Very disappointed with the purchase.",
    ],
    "neutral": [
        "Decent bag overall. Wheels work fine on smooth surfaces but struggle a bit on rough terrain. Build quality is acceptable. Nothing exceptional but gets the job done.",
        "Okay product for occasional travelers. Interior space is good but the divider strap could be better quality. The color looks slightly different from the product images.",
        "Average luggage. Does the job for short trips. Handle could be sturdier. Zipper works fine. Would look at other options if budget allows.",
        "Meets basic requirements. The hard shell is decent quality. Wheels could be smoother. Overall a functional product but not outstanding in any particular way.",
    ],
}

DATES = [
    "January 2024", "February 2024", "March 2024", "April 2024", "May 2024",
    "June 2024", "July 2024", "August 2024", "September 2024", "October 2024",
    "November 2024", "December 2024", "January 2025", "February 2025", "March 2025",
    "April 2025", "May 2025", "June 2025",
]

PRODUCTS_PER_BRAND = 3
REVIEWS_PER_PRODUCT = 5


def make_products() -> list[dict]:
    products = []
    for brand in BRANDS:
        titles = PRODUCT_TITLES[brand["name"]][:PRODUCTS_PER_BRAND]
        for i, title in enumerate(titles):
            asin = f"{brand['asin_prefix']}{i+1:04d}"
            price_lo, price_hi = brand["price_range"]
            mrp = round(random.uniform(price_lo * 1.1, price_hi * 1.3), -2)
            discount_pct = round(random.uniform(10, 45), 1)
            price = round(mrp * (1 - discount_pct / 100), -2)
            rating_lo, rating_hi = brand["rating_range"]
            rating = round(random.uniform(rating_lo, rating_hi), 1)
            review_count = random.randint(120, 4800)

            products.append({
                "asin": asin,
                "title": title,
                "url": f"https://www.amazon.in/dp/{asin}",
                "price": price,
                "mrp": mrp,
                "discount_pct": discount_pct,
                "rating": rating,
                "review_count": review_count,
                "image_url": f"https://m.media-amazon.com/images/I/placeholder_{asin}.jpg",
                "availability": "Available",
                "brand": brand["name"],
            })
    return products


def make_reviews(products: list[dict]) -> list[dict]:
    reviews = []
    for product in products:
        asin = product["asin"]
        brand = product["brand"]
        product_rating = product["rating"]

        for j in range(REVIEWS_PER_PRODUCT):
            # Weight sentiment distribution toward product rating
            roll = random.random()
            if product_rating >= 4.2:
                sentiment = "positive" if roll < 0.70 else ("neutral" if roll < 0.85 else "negative")
            elif product_rating >= 3.8:
                sentiment = "positive" if roll < 0.50 else ("neutral" if roll < 0.75 else "negative")
            else:
                sentiment = "positive" if roll < 0.30 else ("neutral" if roll < 0.55 else "negative")

            if sentiment == "positive":
                rating = random.choice([4, 5])
                title = random.choice(REVIEW_POSITIVE_TITLES)
            elif sentiment == "negative":
                rating = random.choice([1, 2, 3])
                title = random.choice(REVIEW_NEGATIVE_TITLES)
            else:
                rating = random.choice([3, 4])
                title = random.choice(REVIEW_NEUTRAL_TITLES)

            body = random.choice(REVIEW_BODIES[sentiment])
            review_id = f"R{asin}{j:02d}"

            reviews.append({
                "review_id": review_id,
                "title": title,
                "body": body,
                "rating": rating,
                "date": random.choice(DATES),
                "verified_purchase": random.random() > 0.2,
                "helpful_votes": random.randint(0, 45),
                "asin": asin,
                "brand": brand,
            })
    return reviews


if __name__ == "__main__":
    products = make_products()
    reviews = make_reviews(products)

    with open(RAW_DIR / "products_raw.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(products)} products to data/raw/products_raw.json")

    with open(RAW_DIR / "reviews_raw.json", "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(reviews)} reviews to data/raw/reviews_raw.json")
