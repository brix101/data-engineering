import random
from datetime import timedelta

from faker import Faker

from generator.db import copy_rows, get_connection

fake = Faker()

BATCH_SIZE = 10_000

CARRIERS = [
    "J&T Express",
    "LBC Express",
    "Ninja Van",
    "JRS Express",
    "2GO",
]

# Probability that a `processing` order has actually generated a
# shipment row yet (warehouse preparing). Non-processing eligible
# statuses always produce a shipment.
PROCESSING_SHIPMENT_PROBABILITY = 0.40


def get_orders(batch_size: int = BATCH_SIZE):
    with get_connection() as conn:
        with conn.cursor(name="shipment_order_cursor") as cur:
            cur.execute("""
                SELECT id, status, created_at
                FROM orders
                WHERE status IN (
                    'processing',
                    'shipped',
                    'delivered'
                )
                ORDER BY created_at
            """)

            while True:
                rows = cur.fetchmany(batch_size)

                if not rows:
                    break

                yield rows


def derive_shipment_status(order_status: str) -> str:
    """
    Derive a shipment status that is consistent with the parent
    order's lifecycle.
    """

    if order_status == "processing":
        return random.choices(
            ["pending", "shipped"],
            weights=[85, 15],
            k=1,
        )[0]

    if order_status == "shipped":
        return random.choices(
            ["shipped", "in_transit", "lost"],
            weights=[55, 44, 1],
            k=1,
        )[0]

    if order_status == "delivered":
        # A delivered order cannot correspond to a lost shipment.
        return "delivered"

    return "pending"


def generate_shipments(order_batch):
    for order_id, order_status, order_created_at in order_batch:
        # Not every processing order has moved to the shipment stage yet.
        if (
            order_status == "processing"
            and random.random() >= PROCESSING_SHIPMENT_PROBABILITY
        ):
            continue

        shipment_status = derive_shipment_status(order_status)

        shipped_at = None
        delivered_at = None

        if shipment_status in ("shipped", "in_transit", "delivered", "lost"):
            shipped_at = order_created_at + timedelta(
                hours=random.randint(2, 72),
            )

            if shipment_status == "delivered":
                delivered_at = shipped_at + timedelta(
                    days=random.randint(1, 7),
                )

        yield (
            order_id,
            random.choice(CARRIERS),
            f"TRK{fake.random_number(digits=12)}",
            shipment_status,
            shipped_at,
            delivered_at,
        )


def save_shipment_batch(batch):
    copy_rows(
        table="shipments",
        columns=[
            "order_id",
            "carrier",
            "tracking_number",
            "status",
            "shipped_at",
            "delivered_at",
        ],
        rows=batch,
    )


def seed_shipments():
    total = 0

    for order_batch in get_orders():
        batch = list(generate_shipments(order_batch))

        if not batch:
            continue

        save_shipment_batch(batch)

        total += len(batch)

        print(f"Shipments generated: {total:,}")

    print(f"Done! Generated {total:,} shipments.")
