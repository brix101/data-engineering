from db import get_connection

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home & Kitchen",
    "Beauty",
    "Sports",
    "Books",
    "Toys",
    "Automotive",
    "Groceries",
    "Pet Supplies",
    "Health & Wellness",
    "Office Supplies",
    "Garden & Outdoor",
    "Baby Products",
    "Jewelry",
    "Shoes",
    "Watches",
    "Furniture",
    "Appliances",
    "Tools & Hardware",
    "Video Games",
    "Music & Instruments",
    "Movies & TV",
    "Arts & Crafts",
    "Luggage & Travel",
    "Party Supplies",
    "Stationery",
    "Cell Phones & Accessories",
    "Computers & Tablets",
    "Cameras & Photography",
    "Smart Home",
    "Lighting",
    "Bedding & Bath",
    "Kitchen & Dining",
    "Cleaning Supplies",
    "Personal Care",
    "Vitamins & Supplements",
    "Snacks & Beverages",
    "Coffee & Tea",
    "Wine & Spirits",
    "Outdoor Recreation",
    "Fitness Equipment",
    "Cycling",
    "Fishing & Hunting",
    "Camping & Hiking",
    "Board Games & Puzzles",
    "Collectibles",
    "Craft Beer & Brewing",
    "Sewing & Fabric",
    "Industrial & Scientific",
]


def save_categories(categories: list[str]) -> None:
    query = """
        INSERT INTO categories (name)
        VALUES (%s)
        ON CONFLICT (name) DO NOTHING
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, [(category,) for category in categories])


def seed_categories() -> None:
    save_categories(CATEGORIES)
