import random
from uuid import UUID

from generator.db import copy_rows, get_connection

TOTAL_ORDERS = 5_000_000
BATCH_SIZE = 10_000

# Approximate distribution of items per order.
ITEM_COUNT_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8]
ITEM_COUNT_WEIGHTS = [20, 30, 25, 15, 5, 2, 1.5, 1.5]


def get_products() -> list[tuple[UUID, float]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, price
                FROM products
            """)

            return [(row[0], float(row[1])) for row in cur.fetchall()]


def get_orders(
    batch_size: int = BATCH_SIZE,
):
    """
    Read orders in batches so we don't load
    all 5 million orders into memory.
    """

    with get_connection() as conn:
        with conn.cursor(name="order_cursor") as cur:
            cur.execute("""
                SELECT id
                FROM orders
                ORDER BY created_at
            """)

            while True:
                batch = cur.fetchmany(batch_size)

                if not batch:
                    break

                yield [row[0] for row in batch]


def generate_order_items(
    order_ids: list[UUID],
    products: list[tuple[UUID, float]],
):
    for order_id in order_ids:

        item_count = random.choices(
            ITEM_COUNT_OPTIONS,
            weights=ITEM_COUNT_WEIGHTS,
            k=1,
        )[0]

        # Don't sell the same product twice
        # in the same order.
        selected_products = random.sample(
            products,
            k=min(item_count, len(products)),
        )

        for product_id, product_price in selected_products:

            quantity = random.choices(
                [1, 2, 3, 4, 5],
                weights=[65, 20, 8, 5, 2],
                k=1,
            )[0]

            # Most items have no discount. When present, the discount is
            # a percentage off the whole line (quantity * unit_price), which
            # matches how payments.py subtracts it from the subtotal.
            if random.random() < 0.75:
                discount = 0.00
            else:
                discount = round(
                    product_price * quantity * random.uniform(0.05, 0.30),
                    2,
                )

            yield (
                order_id,
                product_id,
                quantity,
                product_price,
                discount,
            )


def save_order_item_batch(batch: list[tuple]) -> None:
    copy_rows(
        table="order_items",
        columns=[
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "discount",
        ],
        rows=batch,
    )


def seed_order_items() -> None:
    products = get_products()

    if not products:
        raise RuntimeError("No products found.")

    print(f"Found {len(products):,} products")
    print("Generating order items...")

    total_items = 0
    order_count = 0

    for order_batch_number, order_batch in enumerate(
        get_orders(),
        start=1,
    ):
        item_batch = []

        for item in generate_order_items(
            order_ids=order_batch,
            products=products,
        ):
            item_batch.append(item)

            if len(item_batch) >= BATCH_SIZE:
                save_order_item_batch(item_batch)

                total_items += len(item_batch)

                item_batch = []

        if item_batch:
            save_order_item_batch(item_batch)
            total_items += len(item_batch)

        order_count += len(order_batch)

        print(
            f"Orders processed: "
            f"{order_count:,}/{TOTAL_ORDERS:,} | "
            f"Items generated: {total_items:,}"
        )

    print(f"Done! Generated " f"{total_items:,} order items.")
