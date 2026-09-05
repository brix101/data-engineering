import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from ingestion.entract import extract_table
from ingestion.parquet import write_parquet_batch
from ingestion.partition import (
    get_or_create_writer,
    get_partition,
    group_by_partition,
)
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


def ingest_table(
    table_name: str,
    primary_key: str,
    required_columns: list[str],
    partition_column: str | None = None,
) -> set[Path]:
    """
    Ingest a table from the source database, validate it, partition it, and write it to Parquet files.
    """

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
        return set()

    schema = TABLE_SCHEMAS.get(table_name)
    if schema is None:
        logger.error("No schema defined for table '%s'", table_name)
        return set()

    total = 0
    batch_counter = 0
    writers = {}
    generated_files = set()
    success = False

    try:
        ingested_at = datetime.now(timezone.utc)

        for batch in extract_table(table_name):
            batch_counter += 1
            total += len(batch)

            # Simulate a random batch failure for testing failure handling.
            # if random.random() < 0.1:
            #     raise RuntimeError(f"simulated random failure at batch {batch_counter}")

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

                generated_files.add(writer.where)

        elapsed = time.perf_counter() - start
        logger.info("extraction runtime: %.2fs", elapsed)

        success = True
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

    if not success:
        return set()

    return generated_files
