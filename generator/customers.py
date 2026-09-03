from datetime import timezone

from faker import Faker

from db import copy_rows

fake = Faker()


def generate_customers(count: int, batch_size: int = 10_000):
    for start in range(0, count, batch_size):
        batch_count = min(batch_size, count - start)

        batch = []

        for i in range(batch_count):
            batch.append(
                (
                    f"customer_{start + i}@example.com",
                    fake.first_name(),
                    fake.last_name(),
                    fake.city(),
                    fake.date_time_between(
                        start_date="-2y",
                        end_date="now",
                        tzinfo=timezone.utc,
                    ),
                )
            )

        yield batch


def save_customer_batch(batch):
    copy_rows(
        table="customers",
        columns=[
            "email",
            "first_name",
            "last_name",
            "city",
            "created_at",
        ],
        rows=batch,
    )


def seed_customers(count: int, batch_size: int = 10_000):
    inserted = 0

    for batch_number, batch in enumerate(
        generate_customers(count, batch_size),
        start=1,
    ):
        save_customer_batch(batch)

        inserted += len(batch)
        percent = inserted / count * 100

        print(
            f"Inserted batch {batch_number}: "
            f"{len(batch):,} customers "
            f"({inserted:,}/{count:,}, {percent:.1f}%)"
        )
