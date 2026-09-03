import random
from datetime import timezone

from faker import Faker

from db import copy_rows, get_connection

fake = Faker()

TOTAL_PRODUCTS = 500_000
BATCH_SIZE = 10_000


def get_sellers() -> list[str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM sellers")
            return [str(row[0]) for row in cur.fetchall()]


def get_categories() -> list[str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories")
            return [str(row[0]) for row in cur.fetchall()]


def generate_product_counts(
    seller_count: int,
    total_products: int,
) -> list[int]:
    """
    Generate a skewed number of products per seller.

    Most sellers get relatively few products,
    while a small number get many products.
    """

    weights = [random.expovariate(1.0) for _ in range(seller_count)]

    total_weight = sum(weights)

    counts = [max(1, int(total_products * weight / total_weight)) for weight in weights]

    # Adjust so the total is exactly total_products.
    difference = total_products - sum(counts)

    while difference > 0:
        index = random.randrange(seller_count)
        counts[index] += 1
        difference -= 1

    while difference < 0:
        index = random.randrange(seller_count)

        if counts[index] > 1:
            counts[index] -= 1
            difference += 1

    return counts


def generate_products(
    sellers: list[str],
    categories: list[str],
    total_products: int,
):
    product_counts = generate_product_counts(
        seller_count=len(sellers),
        total_products=total_products,
    )

    batch = []

    for seller_id, product_count in zip(sellers, product_counts):
        for _ in range(product_count):
            cost = round(random.uniform(5, 500), 2)
            price = round(cost * random.uniform(1.1, 2.5), 2)

            batch.append(
                (
                    seller_id,
                    random.choice(categories),
                    fake.catch_phrase(),
                    price,
                    cost,
                    fake.date_time_between(
                        start_date="-2y",
                        end_date="now",
                        tzinfo=timezone.utc,
                    ),
                )
            )

            if len(batch) >= BATCH_SIZE:
                yield batch
                batch = []

    if batch:
        yield batch


def save_product_batch(batch) -> None:
    copy_rows(
        table="products",
        columns=[
            "seller_id",
            "category_id",
            "name",
            "price",
            "cost",
            "created_at",
        ],
        rows=batch,
    )


def seed_products() -> None:
    sellers = get_sellers()
    categories = get_categories()

    if not sellers:
        raise RuntimeError("No sellers found.")

    if not categories:
        raise RuntimeError("No categories found.")

    print(f"Found {len(sellers):,} sellers")
    print(f"Found {len(categories):,} categories")
    print(f"Generating {TOTAL_PRODUCTS:,} products...")

    total_inserted = 0

    for batch_number, batch in enumerate(
        generate_products(
            sellers=sellers,
            categories=categories,
            total_products=TOTAL_PRODUCTS,
        ),
        start=1,
    ):
        save_product_batch(batch)

        total_inserted += len(batch)

        print(
            f"Batch {batch_number:,}: "
            f"{len(batch):,} products "
            f"({total_inserted:,}/{TOTAL_PRODUCTS:,})"
        )

    print(f"Done! Inserted {total_inserted:,} products.")
