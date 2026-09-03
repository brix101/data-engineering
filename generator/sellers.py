from datetime import timezone

from faker import Faker

from db import get_connection

fake = Faker()


def generate_sellers(count: int) -> list[dict]:
    return [
        {
            "name": fake.company(),
            "created_at": fake.date_time_between(
                start_date="-2y",
                end_date="now",
                tzinfo=timezone.utc,
            ),
        }
        for _ in range(count)
    ]


def save_sellers(sellers: list[dict]) -> None:
    query = """
        INSERT INTO sellers (
            name,
            created_at
        )
        VALUES (
            %(name)s,
            %(created_at)s
        )
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, sellers)


def seed_sellers(count: int) -> None:
    sellers = generate_sellers(count)
    save_sellers(sellers)
