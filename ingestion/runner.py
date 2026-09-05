import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from ingestion.entract import extract_table
from ingestion.parquet import write_parquet_batch
from ingestion.partition import (
    build_object_key,
    get_or_create_writer,
    get_partition,
    group_by_partition,
)
from ingestion.schemas import TABLE_SCHEMAS
from ingestion.storage import (
    ensure_bucket,
    get_s3_client,
    object_exists,
    upload_bucket_file,
    upload_file,
)
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
        "partition_column": "created_at",
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
        "partition_column": "created_at",
        "required_columns": ["id", "name", "created_at"],
    },
    "categories": {
        "primary_key": "id",
        # No natural event time -> partition by ingested_at.
        "partition_column": None,
        "required_columns": ["id", "name"],
    },
    "products": {
        "primary_key": "id",
        "partition_column": "created_at",
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
        "partition_column": "starts_at",
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
        "partition_column": "created_at",
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
        # No natural event time -> partition by ingested_at.
        "partition_column": None,
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
        "partition_column": "paid_at",
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
        "partition_column": "shipped_at",
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
        "partition_column": "created_at",
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
    table_name: str,
    primary_key: str,
    required_columns: list[str],
    partition_column: str | None = None,
) -> None:
    start = time.perf_counter()
    logger.info(
        "Ingesting table '%s' partitioned by '%s'", table_name, partition_column
    )

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
    writers = {}

    try:
        ingested_at = datetime.now(timezone.utc)

        for batch in extract_table(table_name):
            batch_counter += 1
            total += len(batch)

            if partition_column is None:
                # No natural event time -> bucket the whole batch by ingested_at.
                partitions = {get_partition(ingested_at): batch}
            else:
                partitions = group_by_partition(
                    batch,
                    schema.get_field_index(partition_column),
                )

            for partition_key, rows in partitions.items():
                writer = get_or_create_writer(
                    writers,
                    partition_key,
                    table_name,
                    schema,
                )

                write_parquet_batch(
                    writer,
                    rows,
                    schema,
                    ingested_at,
                )

        # upload_file(output_file, "ecommerce-data", output_name)

        # exists = object_exists("ecommerce-data", output_name)

        # if exists:
        #     logger.info("removing local Parquet file '%s'", output_file)
        #     os.remove(output_file)

        elapsed = time.perf_counter() - start
        logger.info("extraction runtime: %.2fs", elapsed)
    except RuntimeError as exc:
        logger.error("Extraction failed for table '%s': %s", table_name, exc)
        logger.error(
            "extraction failed for table '%s' at batch %d after extracting %d rows",
            table_name,
            batch_counter,
            total,
        )
    finally:
        for writer in writers.values():
            writer.close()


if __name__ == "__main__":
    # for table_name, config in TABLE_CONFIG.items():
    #     if table_name != "orders":  # Skip orders table for now
    #         continue
    #
    #     logger.info(config)
    #
    #     ingest_table(
    #         table_name,
    #         config["primary_key"],
    #         config["required_columns"],
    #         config["partition_column"],
    #     )

    bucket_name = "ecommerce-data"
    client = get_s3_client()
    ensure_bucket(client, bucket_name)

    for file_path in Path("data/parquet").rglob("*.parquet"):
        relative_path = file_path.relative_to("data/parquet")
        object_name = relative_path.as_posix()

        upload_file(client, bucket_name, file_path, object_name)

        if object_exists(client, bucket_name, object_name):
            logger.info("removing '%s'", file_path)
            file_path.unlink()
