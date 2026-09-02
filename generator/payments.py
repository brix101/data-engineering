import random
from datetime import timezone
from uuid import UUID

from generator.db import copy_rows, get_connection

BATCH_SIZE = 10_000

PAYMENT_METHODS = [
    "credit_card",
    "debit_card",
    "gcash",
    "maya",
    "bank_transfer",
    "cod",
]

PAYMENT_METHOD_WEIGHTS = [
    30,
    15,
    25,
    15,
    10,
    5,
]

PAYMENT_STATUSES = [
    "completed",
    "failed",
    "pending",
    "refunded",
]

PAYMENT_STATUS_WEIGHTS = [
    90,
    5,
    2,
    3,
]


def get_orders(batch_size: int = BATCH_SIZE):
    with get_connection() as conn:
        with conn.cursor(name="payment_order_cursor") as cur:
            cur.execute("""
                SELECT id, created_at
                FROM orders
                WHERE status != 'cancelled'
                ORDER BY created_at
            """)

            while True:
                rows = cur.fetchmany(batch_size)

                if not rows:
                    break

                yield rows


def generate_payments(order_batch):
    for order_id, order_created_at in order_batch:
        status = random.choices(
            PAYMENT_STATUSES,
            weights=PAYMENT_STATUS_WEIGHTS,
            k=1,
        )[0]

        payment_method = random.choices(
            PAYMENT_METHODS,
            weights=PAYMENT_METHOD_WEIGHTS,
            k=1,
        )[0]

        amount = round(
            random.uniform(20, 5_000),
            2,
        )

        paid_at = None

        if status in ("completed", "refunded"):
            paid_at = order_created_at

        yield (
            order_id,
            amount,
            payment_method,
            status,
            paid_at,
        )


def save_payment_batch(batch):
    copy_rows(
        table="payments",
        columns=[
            "order_id",
            "amount",
            "payment_method",
            "status",
            "paid_at",
        ],
        rows=batch,
    )


def seed_payments():
    total = 0

    for order_batch in get_orders():
        batch = list(generate_payments(order_batch))

        save_payment_batch(batch)

        total += len(batch)

        print(f"Payments generated: {total:,}")

    print(f"Done! Generated {total:,} payments.")
