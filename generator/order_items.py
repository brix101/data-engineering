import random
from datetime import timedelta

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


def get_orders_with_totals(batch_size: int = BATCH_SIZE):
    """
    Get orders together with their actual totals.

    The total is calculated from order_items instead
    of generating a random payment amount.
    """

    with get_connection() as conn:
        with conn.cursor(name="payment_order_cursor") as cur:
            cur.execute("""
                SELECT
                    o.id,
                    o.created_at,
                    o.shipping_fee,
                    COALESCE(
                        SUM(
                            (oi.quantity * oi.unit_price)
                            - oi.discount
                        ),
                        0
                    ) AS subtotal
                FROM orders o
                JOIN order_items oi
                    ON oi.order_id = o.id
                WHERE o.status != 'cancelled'
                GROUP BY
                    o.id,
                    o.created_at,
                    o.shipping_fee
                ORDER BY o.created_at
            """)

            while True:
                rows = cur.fetchmany(batch_size)

                if not rows:
                    break

                yield rows


def generate_payments(order_batch):
    for (
        order_id,
        order_created_at,
        shipping_fee,
        subtotal,
    ) in order_batch:

        amount = round(
            float(subtotal) + float(shipping_fee),
            2,
        )

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

        paid_at = None

        if status in ("completed", "refunded"):
            paid_at = order_created_at + timedelta(minutes=random.randint(1, 30))

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


def generate_and_save_payments():
    total = 0

    for order_batch in get_orders_with_totals():
        batch = list(generate_payments(order_batch))

        if not batch:
            continue

        save_payment_batch(batch)

        total += len(batch)

        print(f"Payments generated: {total:,}")

    print(f"Done! Generated {total:,} payments.")


if __name__ == "__main__":
    generate_and_save_payments()
