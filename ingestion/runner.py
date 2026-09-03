import logging
import time
from datetime import datetime, timezone
from uuid import UUID

import pyarrow as pa
import pyarrow.parquet as pq

from ingestion.extractor import extract_table
from ingestion.parquet import write_parquet_file
from ingestion.schemas import TABLE_SCHEMAS
from ingestion.validate import (
    validate_primary_key_not_null,
    validate_required_columns,
    validate_table_exists,
    validate_table_not_empty,
    validate_unique_primary_key,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

TABLE_CONFIG = {
    "customers": {
        "primary_key": "id",
        "required_columns": [
            "id",
            "email",
            "first_name",
            "last_name",
            "city",
            "created_at",
        ],
    },
    "sellers": {
        "primary_key": "id",
        "required_columns": ["id", "name", "created_at"],
    },
    "categories": {
        "primary_key": "id",
        "required_columns": ["id", "name"],
    },
    "products": {
        "primary_key": "id",
        "required_columns": [
            "id",
            "seller_id",
            "category_id",
            "name",
            "price",
            "cost",
            "created_at",
        ],
    },
    "coupons": {
        "primary_key": "id",
        "required_columns": [
            "id",
            "code",
            "discount_type",
            "discount_value",
            "starts_at",
            "expires_at",
        ],
    },
    "orders": {
        "primary_key": "id",
        "required_columns": [
            "id",
            "customer_id",
            "created_at",
            "status",
            "shipping_fee",
        ],
    },
    "order_items": {
        "primary_key": "id",
        "required_columns": [
            "id",
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "discount",
        ],
    },
    "payments": {
        "primary_key": "id",
        "required_columns": [
            "id",
            "order_id",
            "amount",
            "payment_method",
            "status",
        ],
    },
    "shipments": {
        "primary_key": "id",
        "required_columns": [
            "id",
            "order_id",
            "carrier",
            "tracking_number",
            "status",
        ],
    },
    "returns": {
        "primary_key": "id",
        "required_columns": [
            "id",
            "order_item_id",
            "quantity",
            "reason",
            "status",
            "created_at",
        ],
    },
}


def ingest_table(
    table_name: str, primary_key: str, required_columns: list[str]
) -> None:
    start = time.perf_counter()

    try:
        validate_table_exists(table_name)
        validate_required_columns(table_name, required_columns)
        validate_primary_key_not_null(table_name, primary_key)
        validate_unique_primary_key(table_name, primary_key)
        validate_table_not_empty(table_name)

    except ValueError as exc:
        logger.error("Validation failed for table '%s': %s", table_name, exc)
        return

    schema = TABLE_SCHEMAS.get(table_name)
    if schema is None:
        logger.error("No schema defined for table '%s'", table_name)
        return

    total = 0
    batch_counter = 0
    try:
        ingested_at = datetime.now(timezone.utc)

        for batch_number, batch in enumerate(extract_table(table_name), start=1):
            batch_counter += 1
            total += len(batch)

            write_parquet_file(
                table_name,
                batch,
                schema,
                ingested_at,
            )

        elapsed = time.perf_counter() - start
        logger.info("extracted %d rows from table '%s'", total, table_name)
        logger.info("extraction runtime: %.2fs", elapsed)
    except RuntimeError as exc:
        logger.error("Extraction failed for table '%s': %s", table_name, exc)
        logger.error(
            "extraction failed for table '%s' at batch %d after extracting %d rows",
            table_name,
            batch_counter,
            total,
        )
        return


if __name__ == "__main__":
    for table_name, config in TABLE_CONFIG.items():
        if table_name != "customers":
            continue

        ingest_table(
            table_name,
            config["primary_key"],
            config["required_columns"],
        )
