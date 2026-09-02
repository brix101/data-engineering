import random
from datetime import datetime, timedelta, timezone

from generator.db import copy_rows, get_connection

BATCH_SIZE = 10_000

# Realistic-ish return rates by category. Consumables rarely come back,
# apparel comes back the most (size/fit), electronics are moderate.
DEFAULT_RETURN_RATE = 0.05

CATEGORY_RETURN_RATES = {
    "Electronics": 0.12,
    "Clothing": 0.18,
    "Home & Kitchen": 0.06,
    "Beauty": 0.07,
    "Sports": 0.08,
    "Books": 0.03,
    "Toys": 0.07,
    "Automotive": 0.06,
    "Groceries": 0.01,
    "Pet Supplies": 0.05,
    "Health & Wellness": 0.04,
    "Office Supplies": 0.04,
    "Garden & Outdoor": 0.06,
    "Baby Products": 0.07,
    "Jewelry": 0.15,
    "Shoes": 0.20,
    "Watches": 0.12,
    "Furniture": 0.08,
    "Appliances": 0.10,
    "Tools & Hardware": 0.06,
    "Video Games": 0.04,
    "Music & Instruments": 0.06,
    "Movies & TV": 0.03,
    "Arts & Crafts": 0.04,
    "Luggage & Travel": 0.10,
    "Party Supplies": 0.03,
    "Stationery": 0.03,
    "Cell Phones & Accessories": 0.13,
    "Computers & Tablets": 0.14,
    "Cameras & Photography": 0.12,
    "Smart Home": 0.11,
    "Lighting": 0.07,
    "Bedding & Bath": 0.08,
    "Kitchen & Dining": 0.06,
    "Cleaning Supplies": 0.02,
    "Personal Care": 0.03,
    "Vitamins & Supplements": 0.03,
    "Snacks & Beverages": 0.01,
    "Coffee & Tea": 0.02,
    "Wine & Spirits": 0.02,
    "Outdoor Recreation": 0.08,
    "Fitness Equipment": 0.09,
    "Cycling": 0.08,
    "Fishing & Hunting": 0.06,
    "Camping & Hiking": 0.07,
    "Board Games & Puzzles": 0.04,
    "Collectibles": 0.05,
    "Craft Beer & Brewing": 0.02,
    "Sewing & Fabric": 0.05,
    "Industrial & Scientific": 0.05,
}

RETURN_REASONS = [
    "defective",
    "wrong_item",
    "damaged",
    "not_as_described",
    "changed_mind",
    "wrong_size",
]

# Default weights when no category-specific bias applies.
DEFAULT_REASON_WEIGHTS = [20, 15, 15, 15, 20, 15]

# Categories where size/fit is the dominant return reason.
SIZE_HEAVY_CATEGORIES = {"Clothing", "Shoes", "Jewelry", "Watches"}
SIZE_HEAVY_REASON_WEIGHTS = [10, 5, 10, 10, 15, 50]

# Categories where defects/damage dominate.
DEFECT_HEAVY_CATEGORIES = {
    "Electronics",
    "Cell Phones & Accessories",
    "Computers & Tablets",
    "Cameras & Photography",
    "Smart Home",
    "Appliances",
}
DEFECT_HEAVY_REASON_WEIGHTS = [45, 10, 20, 10, 10, 5]

# Fragile / damage-prone categories.
DAMAGE_HEAVY_CATEGORIES = {"Furniture", "Lighting", "Kitchen & Dining"}
DAMAGE_HEAVY_REASON_WEIGHTS = [15, 10, 40, 15, 15, 5]

# Skewed return quantities: most returns are for a single unit.
QUANTITY_WEIGHTS = [
    (1, 0.85),
    (2, 0.12),
    (3, 0.03),
]


def get_reason_weights(category_name: str) -> list[int]:
    if category_name in SIZE_HEAVY_CATEGORIES:
        return SIZE_HEAVY_REASON_WEIGHTS

    if category_name in DEFECT_HEAVY_CATEGORIES:
        return DEFECT_HEAVY_REASON_WEIGHTS

    if category_name in DAMAGE_HEAVY_CATEGORIES:
        return DAMAGE_HEAVY_REASON_WEIGHTS

    return DEFAULT_REASON_WEIGHTS


def pick_return_quantity(available: int) -> int:
    values = [v for v, _ in QUANTITY_WEIGHTS]
    weights = [w for _, w in QUANTITY_WEIGHTS]

    chosen = random.choices(values, weights=weights, k=1)[0]

    return min(chosen, available)


def derive_return_status(created_at: datetime, now: datetime) -> str:
    """
    Correlate the return's status with how old the request is.

    Fresh requests are still in triage, old ones have run their course.
    """

    age_days = (now - created_at).days

    if age_days < 3:
        return random.choices(
            ["requested", "approved", "rejected"],
            weights=[80, 15, 5],
            k=1,
        )[0]

    if age_days < 14:
        return random.choices(
            ["approved", "rejected", "requested", "completed"],
            weights=[55, 20, 10, 15],
            k=1,
        )[0]

    return random.choices(
        ["completed", "rejected", "approved"],
        weights=[80, 15, 5],
        k=1,
    )[0]


def get_order_items(batch_size: int = BATCH_SIZE):
    """
    Stream order_items from delivered orders together with the
    product's category name and (best-effort) delivery timestamp.

    When a shipment row is missing we fall back to
    `orders.created_at + 3 days` so a return is never dated earlier
    than a plausible delivery date.
    """

    with get_connection() as conn:
        with conn.cursor(name="return_item_cursor") as cur:
            cur.execute("""
                SELECT
                    oi.id,
                    oi.quantity,
                    c.name AS category_name,
                    COALESCE(
                        s.delivered_at,
                        o.created_at + interval '3 days'
                    ) AS reference_at
                FROM order_items oi
                JOIN orders o
                    ON o.id = oi.order_id
                JOIN products p
                    ON p.id = oi.product_id
                JOIN categories c
                    ON c.id = p.category_id
                LEFT JOIN shipments s
                    ON s.order_id = o.id
                WHERE o.status = 'delivered'
                ORDER BY oi.id
            """)

            while True:
                rows = cur.fetchmany(batch_size)

                if not rows:
                    break

                yield rows


def generate_returns(item_batch, now: datetime):
    for order_item_id, quantity, category_name, reference_at in item_batch:
        return_rate = CATEGORY_RETURN_RATES.get(
            category_name,
            DEFAULT_RETURN_RATE,
        )

        if random.random() >= return_rate:
            continue

        return_quantity = pick_return_quantity(quantity)

        reason = random.choices(
            RETURN_REASONS,
            weights=get_reason_weights(category_name),
            k=1,
        )[0]

        # A return is filed 1-30 days after delivery (fallback to order date).
        created_at = reference_at + timedelta(
            days=random.randint(1, 30),
            hours=random.randint(0, 23),
        )

        # Never let the return be in the future relative to "now".
        created_at = min(created_at, now)

        status = derive_return_status(created_at=created_at, now=now)

        yield (
            order_item_id,
            return_quantity,
            reason,
            status,
            created_at,
        )


def save_return_batch(batch):
    copy_rows(
        table="returns",
        columns=[
            "order_item_id",
            "quantity",
            "reason",
            "status",
            "created_at",
        ],
        rows=batch,
    )


def seed_returns():
    now = datetime.now(timezone.utc)

    total = 0

    for item_batch in get_order_items():
        batch = list(generate_returns(item_batch, now=now))

        if not batch:
            continue

        save_return_batch(batch)

        total += len(batch)

        print(f"Returns generated: {total:,}")

    print(f"Done! Generated {total:,} returns.")
