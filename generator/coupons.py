import random
from datetime import timedelta, timezone

from faker import Faker

from db import copy_rows

fake = Faker()

TOTAL_COUPONS = 100_000
BATCH_SIZE = 10_000


def generate_coupons(
    count: int = TOTAL_COUPONS,
    batch_size: int = BATCH_SIZE,
):
    batch = []

    for i in range(1, count + 1):
        discount_type = random.choice(
            [
                "percentage",
                "fixed",
            ]
        )

        if discount_type == "percentage":
            discount_value = round(
                random.uniform(5, 30),
                2,
            )
        else:
            discount_value = round(
                random.uniform(5, 100),
                2,
            )

        starts_at = fake.date_time_between(
            start_date="-2y",
            end_date="-30d",
            tzinfo=timezone.utc,
        )

        expires_at = starts_at + timedelta(days=random.randint(7, 90))

        batch.append(
            (
                f"SAVE{i:06d}",
                discount_type,
                discount_value,
                round(random.uniform(50, 1_000), 2),
                starts_at,
                expires_at,
            )
        )

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def save_coupon_batch(batch) -> None:
    copy_rows(
        table="coupons",
        columns=[
            "code",
            "discount_type",
            "discount_value",
            "minimum_order_amount",
            "starts_at",
            "expires_at",
        ],
        rows=batch,
    )


def seed_coupons() -> None:
    total_inserted = 0

    for batch_number, batch in enumerate(
        generate_coupons(),
        start=1,
    ):
        save_coupon_batch(batch)

        total_inserted += len(batch)

        print(
            f"Batch {batch_number:,}: "
            f"{len(batch):,} coupons "
            f"({total_inserted:,}/{TOTAL_COUPONS:,})"
        )

    print(f"Done! Inserted {total_inserted:,} coupons.")
