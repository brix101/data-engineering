import random
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from generator.db import copy_rows, get_connection

TWO_PLACES = Decimal("0.01")
ZERO = Decimal(0)
HUNDRED = Decimal(100)

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


def get_orders_with_totals(batch_size: int = BATCH_SIZE):
    """
    Stream orders together with their real subtotal (from order_items)
    and any assigned coupon's discount type/value.
    """

    with get_connection() as conn:
        with conn.cursor(name="payment_order_cursor") as cur:
            cur.execute("""
                SELECT
                    o.id,
                    o.status,
                    o.created_at,
                    o.shipping_fee,
                    COALESCE(
                        SUM(
                            (oi.quantity * oi.unit_price) - oi.discount
                        ),
                        0
                    ) AS subtotal,
                    c.discount_type,
                    c.discount_value
                FROM orders o
                JOIN order_items oi
                    ON oi.order_id = o.id
                LEFT JOIN coupons c
                    ON c.id = o.coupon_id
                GROUP BY
                    o.id,
                    o.status,
                    o.created_at,
                    o.shipping_fee,
                    c.discount_type,
                    c.discount_value
                ORDER BY o.created_at
            """)

            while True:
                rows = cur.fetchmany(batch_size)

                if not rows:
                    break

                yield rows


def compute_payment_amount(
    subtotal: Decimal,
    shipping_fee: Decimal,
    discount_type: str | None,
    discount_value: Decimal | None,
) -> Decimal:
    """
    Apply the coupon discount to the subtotal before adding shipping.

    - Percentage: subtotal * value / 100
    - Fixed: value
    - Clamped so the discounted subtotal never goes below zero.
    - Shipping is added on top and is not discountable.
    """

    discount = ZERO

    if discount_type == "percentage" and discount_value is not None:
        discount = subtotal * discount_value / HUNDRED
    elif discount_type == "fixed" and discount_value is not None:
        discount = discount_value

    discount = min(discount, subtotal)

    total = subtotal - discount + shipping_fee

    return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def derive_payment_status_and_paid_at(
    order_status: str,
    order_created_at,
):
    """
    Correlate payment status/timestamps with the order lifecycle.
    """

    if order_status == "pending":
        return "pending", None

    if order_status in ("paid", "processing", "shipped", "delivered"):
        paid_at = order_created_at + timedelta(minutes=random.randint(1, 30))
        return "completed", paid_at

    if order_status == "cancelled":
        # Roughly: 60% never paid, 30% paid then refunded, 10% payment failed.
        roll = random.random()

        if roll < 0.60:
            return "failed", None

        if roll < 0.90:
            paid_at = order_created_at + timedelta(minutes=random.randint(1, 30))
            return "refunded", paid_at

        return "failed", None

    # Fallback (shouldn't happen given the CHECK constraint).
    return "pending", None


def generate_payments(order_batch):
    for (
        order_id,
        order_status,
        order_created_at,
        shipping_fee,
        subtotal,
        discount_type,
        discount_value,
    ) in order_batch:
        amount = compute_payment_amount(
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            discount_type=discount_type,
            discount_value=discount_value,
        )

        status, paid_at = derive_payment_status_and_paid_at(
            order_status=order_status,
            order_created_at=order_created_at,
        )

        payment_method = random.choices(
            PAYMENT_METHODS,
            weights=PAYMENT_METHOD_WEIGHTS,
            k=1,
        )[0]

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

    for order_batch in get_orders_with_totals():
        batch = list(generate_payments(order_batch))

        if not batch:
            continue

        save_payment_batch(batch)

        total += len(batch)

        print(f"Payments generated: {total:,}")

    print(f"Done! Generated {total:,} payments.")
