import random
from uuid import UUID

from generator.db import copy_rows, get_connection

BATCH_SIZE = 10_000

RETURN_REASONS = [
    "defective",
    "wrong_item",
    "damaged",
    "not_as_described",
    "changed_mind",
    "wrong_size",
]

RETURN_REASON_WEIGHTS = [
    20,
    15,
    15,
    15,
    20,
    15,
]

RETURN_STATUSES = [
    "requested",
    "approved",
    "rejected",
    "completed",
]

RETURN_STATUS_WEIGHTS = [
    10,
    20,
    10,
    60,
]


def get_order_items(batch_size: int = BATCH_SIZE):
    with get_connection() as conn:
        with conn.cursor(name="return_item_cursor") as cur:
            cur.execute("""
                SELECT
                    oi.id,
                    oi.quantity
                FROM order_items oi
                JOIN orders o
                    ON o.id = oi.order_id
                WHERE o.status = 'delivered'
                ORDER BY oi.id
            """)

            while True:
                rows = cur.fetchmany(batch_size)

                if not rows:
                    break

                yield rows


def generate_returns(item_batch):
    for order_item_id, quantity in item_batch:

        # Only some delivered items are returned.
        if random.random() > 0.08:
            continue

        return_quantity = random.randint(
            1,
            quantity,
        )

        reason = random.choices(
            RETURN_REASONS,
            weights=RETURN_REASON_WEIGHTS,
            k=1,
        )[0]

        status = random.choices(
            RETURN_STATUSES,
            weights=RETURN_STATUS_WEIGHTS,
            k=1,
        )[0]

        yield (
            order_item_id,
            return_quantity,
            reason,
            status,
        )


def save_return_batch(batch):
    copy_rows(
        table="returns",
        columns=[
            "order_item_id",
            "quantity",
            "reason",
            "status",
        ],
        rows=batch,
    )


def seed_returns():
    total = 0

    for item_batch in get_order_items():
        batch = list(generate_returns(item_batch))

        if not batch:
            continue

        save_return_batch(batch)

        total += len(batch)

        print(f"Returns generated: {total:,}")

    print(f"Done! Generated {total:,} returns.")
