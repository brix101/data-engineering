from psycopg import sql

from db import get_connection


def validate_required_columns(
    table_name: str,
    required_columns: list[str],
) -> None:
    """
    Validate that the specified table contains the required columns.

    Args:
        table_name (str): The name of the table to validate.
        required_columns (list[str]): A list of required column names.

    Raises:
        ValueError: If any required columns are missing from the table.
    """

    if not required_columns:
        raise ValueError("required_columns list cannot be empty")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = %s"
                ),
                [table_name],
            )
            existing_columns = {row[0] for row in cur.fetchall()}

    missing_columns = set(required_columns) - existing_columns

    if missing_columns:
        raise ValueError(
            f"Missing required columns in '{table_name}': {', '.join(missing_columns)}"
        )


def validate_primary_key_not_null(
    table_name: str,
    primary_key: str,
) -> None:
    """
    Validate that the specified primary key column does not contain NULL values.

    Args:
        table_name (str): The name of the table to validate.
        primary_key_column (str): The name of the primary key column.

    Raises:
        ValueError: If any NULL values are found in the primary key column.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {} WHERE {} IS NULL").format(
                    sql.Identifier(table_name),
                    sql.Identifier(primary_key),
                )
            )
            row = cur.fetchone()
            null_count = row[0] if row else 0

    if null_count > 0:
        raise ValueError(
            f"Primary key column '{primary_key}' in table '{table_name}' contains {null_count} NULL values."
        )


def validate_unique_primary_key(
    table_name: str,
    primary_key: str,
) -> None:
    """
    Validate that the specified primary key column contains unique values.

    Args:
        table_name (str): The name of the table to validate.
        primary_key_column (str): The name of the primary key column.

    Raises:
        ValueError: If any duplicate values are found in the primary key column.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT COUNT(*) - COUNT(DISTINCT {}) FROM {}").format(
                    sql.Identifier(primary_key),
                    sql.Identifier(table_name),
                )
            )
            row = cur.fetchone()
            duplicate_count = row[0] if row else 0

    if duplicate_count > 0:
        raise ValueError(
            f"Primary key column '{primary_key}' in table '{table_name}' contains {duplicate_count} duplicate values."
        )


def validate_table_exists(table_name: str) -> None:
    """
    Validate that the specified table exists in the database.

    Args:
        table_name (str): The name of the table to validate.

    Raises:
        ValueError: If the specified table does not exist.
    """

    with get_connection() as conn:
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


def validate_table_not_empty(table_name: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name))
            )
            row = cur.fetchone()
            row_count = row[0] if row else 0

    if row_count == 0:
        raise ValueError(f"Table '{table_name}' is empty.")
