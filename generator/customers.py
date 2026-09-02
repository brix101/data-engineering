from datetime import timezone

from faker import Faker

from generator.db import get_connection

fake = Faker()


def generate_customers(count: int):
    customers = []

    for _ in range(count):
        customers.append(
            {
                "email": fake.unique.email(),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "city": fake.city(),
                "created_at": fake.date_time_between(
                    start_date="-2y", end_date="now", tzinfo=timezone.utc
                ),
            }
        )

    return customers


def save_customers(customers: list[dict]) -> None:
    query = """
        INSERT INTO customers (
            email,
            first_name,
            last_name,
            city,
            created_at
        )
        VALUES (
            %(email)s,
            %(first_name)s,
            %(last_name)s,
            %(city)s,
            %(created_at)s
        )
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, customers)

        conn.commit()


if __name__ == "__main__":
    customers = generate_customers(100)
    save_customers(customers)

    print(f"Inserted {len(customers)} customers")
