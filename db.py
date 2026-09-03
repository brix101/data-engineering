import os
from collections.abc import Iterable
from typing import Any

import psycopg
from psycopg import OperationalError, sql

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ecommerce:ecommerce@localhost:5432/ecommerce",
)


def get_connection():
    try:
        return psycopg.connect(DATABASE_URL)
    except OperationalError as e:
        print(f"[error] failed to connect to database: {e}")
        raise


def copy_rows(
    table: str,
    columns: list[str],
    rows: Iterable[tuple[Any, ...]],
) -> None:
    query = sql.SQL("COPY {} ({}) FROM STDIN").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            with cur.copy(query) as copy:
                for row in rows:
                    copy.write_row(row)
