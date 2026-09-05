import logging
from contextlib import contextmanager

from psycopg import sql

from db import get_connection

logger = logging.getLogger(__name__)


class Table:
    """
    A validated table handle returned by ``Validator.get_table``.

    Carries the table name so downstream checks read fluently, e.g.::

        table = validator.get_table("users")
        table.required_columns(["id", "name"])
        table.primary_key_not_null("id")
        table.unique_primary_key("id")
        table.not_empty()
    """

    def __init__(self, table_name: str, conn=None):
        self.table_name = table_name
        self.conn = conn

    @contextmanager
    def _conn_context(self):
        """Yield a connection, closing it only if we opened it ourselves.

        psycopg3's ``Connection.__exit__`` calls ``close()``, so wrapping an
        injected connection in ``with`` would close it after the first check
        and break every subsequent validation call on this ``Table``.
        """
        if self.conn is not None:
            yield self.conn
        else:
            with get_connection() as conn:
                yield conn

    def required_columns(self, required_columns: list[str]) -> "Table":
        """
        Validate that this table contains the required columns.

        Args:
            required_columns (list[str]): A list of required column names.

        Raises:
            ValueError: If any required columns are missing from the table.
        """

        logger.info("validating required columns")

        if not required_columns:
            raise ValueError("required_columns list cannot be empty")

        with self._conn_context() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "SELECT column_name FROM information_schema.columns WHERE table_name = %s"
                    ),
                    [self.table_name],
                )
                existing_columns = {row[0] for row in cur.fetchall()}

        missing_columns = set(required_columns) - existing_columns

        if missing_columns:
            raise ValueError(
                f"Missing required columns in '{self.table_name}': {', '.join(missing_columns)}"
            )

        return self

    def primary_key_not_null(self, primary_key: str) -> "Table":
        """
        Validate that the specified primary key column does not contain NULL values.

        Args:
            primary_key (str): The name of the primary key column.

        Raises:
            ValueError: If any NULL values are found in the primary key column.
        """

        logger.info("validating primary key '%s' for non-null values", primary_key)

        if primary_key:
            logger.info(
                "Skipping! let postgres handle nulls, since it is more efficient than checking in Python."
            )
            return self

        with self._conn_context() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT COUNT(*) FROM {} WHERE {} IS NULL").format(
                        sql.Identifier(self.table_name),
                        sql.Identifier(primary_key),
                    )
                )
                row = cur.fetchone()
                null_count = row[0] if row else 0

        if null_count > 0:
            raise ValueError(
                f"Primary key column '{primary_key}' in table '{self.table_name}' contains {null_count} NULL values."
            )

        return self

    def unique_primary_key(self, primary_key: str) -> "Table":
        """
        Validate that the specified primary key column contains unique values.

        Fails fast on the first duplicate group instead of computing
        ``COUNT(*) - COUNT(DISTINCT pk)`` over the entire table. ``LIMIT 1``
        lets Postgres stop as soon as a duplicated group is found, which is
        especially cheap when ``pk`` is indexed (GroupAggregate over sorted
        input can short-circuit).

        Args:
            primary_key (str): The name of the primary key column.

        Raises:
            ValueError: If any duplicate values are found in the primary key column.
        """

        logger.info("validating primary key '%s' for uniqueness", primary_key)

        if primary_key:
            logger.info(
                "Skipping! let postgres handle uniqueness, since it is more efficient than checking in Python."
            )
            return self

        with self._conn_context() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "SELECT {pk}, COUNT(*) AS c "
                        "FROM {tbl} "
                        "GROUP BY {pk} "
                        "HAVING COUNT(*) > 1 "
                        "LIMIT 1"
                    ).format(
                        pk=sql.Identifier(primary_key),
                        tbl=sql.Identifier(self.table_name),
                    )
                )
                row = cur.fetchone()

        if row is not None:
            duplicate_value, occurrences = row
            raise ValueError(
                f"Primary key column '{primary_key}' in table '{self.table_name}' "
                f"contains duplicate value {duplicate_value!r} ({occurrences} occurrences)."
            )

        return self

    def not_empty(self) -> "Table":
        """
        Validate that this table has at least one row.

        Uses ``SELECT 1 ... LIMIT 1`` rather than ``COUNT(*)`` so Postgres
        stops at the first visible tuple instead of scanning the whole table.

        Raises:
            ValueError: If the table is empty.
        """

        logger.info("validating that table '%s' is not empty", self.table_name)

        with self._conn_context() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT 1 FROM {} LIMIT 1").format(
                        sql.Identifier(self.table_name)
                    )
                )
                has_row = cur.fetchone() is not None

        if not has_row:
            raise ValueError(f"Table '{self.table_name}' is empty.")

        return self


class Validator:
    def __init__(self, conn=None):
        # Do not eagerly open a connection: any `with self.conn` in a check
        # method would close it (psycopg3 closes on __exit__), leaving the
        # validator permanently broken after the first call.
        self.conn = conn

    @contextmanager
    def _conn_context(self):
        if self.conn is not None:
            yield self.conn
        else:
            with get_connection() as conn:
                yield conn

    def get_table(self, table_name: str) -> Table:
        """
        Fetch a validated handle to the specified table.

        Verifies that the table exists in the database and returns a
        ``Table`` instance for chained validation checks.

        Args:
            table_name (str): The name of the table to fetch.

        Returns:
            Table: A handle to the validated table for chained checks.

        Raises:
            ValueError: If the specified table does not exist.
        """

        with self._conn_context() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)"
                    ),
                    [table_name],
                )
                rows = cur.fetchone()
                exists = rows[0] if rows else False

        if not exists:
            raise ValueError(f"Table '{table_name}' does not exist in the database.")

        return Table(table_name, conn=self.conn)
