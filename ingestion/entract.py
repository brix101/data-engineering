import logging
from collections.abc import Iterator

from psycopg import sql

from db import get_connection

BATCH_SIZE = 10_000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def extract_table(
    table: str,
    batch_size: int = BATCH_SIZE,
) -> Iterator[list[tuple]]:
    """Yield all rows from a table in batches using a server-side (named) cursor.

    Args:
        batch_size: rows per yielded batch (default 10k).
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than 0")

    logger.info(f"extracting table '{table}'")
    with get_connection() as conn:
        with conn.cursor(name=f"extract_{table}") as cur:
            cur.itersize = batch_size
            cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table)))

            batch_counter = 0
            while True:
                rows = cur.fetchmany(batch_size)
                if not rows:
                    break

                batch_counter += 1
                logger.info(
                    "table=%s batch=%d rows=%d",
                    table,
                    batch_counter,
                    len(rows),
                )
                yield rows
