import random
from datetime import timezone
from uuid import UUID, uuid4

from faker import Faker

from db import copy_rows, get_connection

fake = Faker()

TOTAL_ORDERS = 5_000_000
BATCH_SIZE = 10_000

ORDER_STATUSES = [
    "pending",
    "paid",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
]

STATUS_WEIGHTS = [
    3,  # pending
    7,  # paid
    5,  # processing
    10,  # shipped
    68,  # delivered
    7,  # cancelled
]


def get_customers() -> list[UUID]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM customers")
            return [row[0] for row in cur.fetchall()]


def create_customer_groups(
    customers: list[UUID],
) -> tuple[
    list[UUID],
    list[UUID],
    list[UUID],
    list[UUID],
]:
    """
    Split customers into activity groups.

    VIP:
        1% of customers

    Frequent:
        9% of customers

    Occasional:
        30% of customers

    Rare:
        60% of customers
    """

    customers = customers.copy()
    random.shuffle(customers)

    total = len(customers)

    vip_end = int(total * 0.01)
    frequent_end = int(total * 0.10)
    occasional_end = int(total * 0.40)

    vip = customers[:vip_end]
    frequent = customers[vip_end:frequent_end]
    occasional = customers[frequent_end:occasional_end]
    rare = customers[occasional_end:]

    return vip, frequent, occasional, rare


def choose_customer(
    vip: list[UUID],
    frequent: list[UUID],
    occasional: list[UUID],
    rare: list[UUID],
) -> UUID:
    """
    Choose a customer based on their activity level.
    """

    group = random.choices(
        [vip, frequent, occasional, rare],
        weights=[15, 4, 1, 0.2],
        k=1,
    )[0]

    return random.choice(group)


def generate_orders(
    customers: list[UUID],
    total_orders: int = TOTAL_ORDERS,
    batch_size: int = BATCH_SIZE,
):
    vip, frequent, occasional, rare = create_customer_groups(customers)

    batch = []

    for _ in range(total_orders):
        order_id = uuid4()

        customer_id = choose_customer(
            vip=vip,
            frequent=frequent,
            occasional=occasional,
            rare=rare,
        )

        # Coupons are assigned in a separate post-order_items step
        # so we can validate minimum_order_amount against the real subtotal.
        coupon_id = None

        status = random.choices(
            ORDER_STATUSES,
            weights=STATUS_WEIGHTS,
            k=1,
        )[0]

        created_at = fake.date_time_between(
            start_date="-2y",
            end_date="now",
            tzinfo=timezone.utc,
        )

        shipping_fee = round(
            random.uniform(0, 300),
            2,
        )

        batch.append(
            (
                order_id,
                customer_id,
                coupon_id,
                created_at,
                status,
                shipping_fee,
            )
        )

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def save_order_batch(
    batch: list[tuple],
) -> None:
    copy_rows(
        table="orders",
        columns=[
            "id",
            "customer_id",
            "coupon_id",
            "created_at",
            "status",
            "shipping_fee",
        ],
        rows=batch,
    )


def seed_orders() -> None:
    customers = get_customers()

    if not customers:
        raise RuntimeError("No customers found.")

    print(f"Found {len(customers):,} customers")
    print(f"Generating {TOTAL_ORDERS:,} orders...")

    total_inserted = 0

    for batch_number, batch in enumerate(
        generate_orders(
            customers=customers,
        ),
        start=1,
    ):
        save_order_batch(batch)

        total_inserted += len(batch)

        print(
            f"Batch {batch_number:,}: "
            f"{len(batch):,} orders "
            f"({total_inserted:,}/{TOTAL_ORDERS:,})"
        )

    print(f"Done! Inserted {total_inserted:,} orders.")
