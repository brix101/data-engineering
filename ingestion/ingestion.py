import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from ingestion.entract import extract_table
from ingestion.partition import PartitionWriterManager
from ingestion.schemas import TABLE_SCHEMAS
from ingestion.validate import Validator

logger = logging.getLogger(__name__)


validate = Validator()
pa_manager = PartitionWriterManager()


def ingest_table(table_name: str, config: dict) -> set[Path]:
    """
    Ingest a table from the source database, validate it, partition it, and write it to Parquet files.
    """

    start = time.perf_counter()
    logger.info("ingesting table '%s'", table_name)

    try:
        table = validate.get_table(table_name)
        table.required_columns(config["required_columns"])
        table.primary_key_not_null(config["primary_key"])
        table.unique_primary_key(config["primary_key"])
        table.not_empty()

    except ValueError as exc:
        logger.error("validation failed: %s", exc)
        return set()

    schema = TABLE_SCHEMAS.get(table_name)
    if schema is None:
        logger.error("no schema defined")
        return set()

    batches_processed = 0
    rows_processed = 0
    failed_batch: int | None = None

    try:
        generated_files: set[Path] = set()
        ingested_at = datetime.now(timezone.utc)

        column = config.get("partition_column")
        partition_index = schema.get_field_index(column) if column else None

        for batch_number, batch in enumerate(extract_table(table_name), start=1):
            try:
                # Simulate a random batch failure for testing failure handling.
                # if random.random() < 0.1:
                #     raise RuntimeError("simulated random failure")

                partitions = pa_manager.partition(batch, ingested_at, partition_index)

                for partition_key, rows in partitions.items():
                    handler = pa_manager.get_writer(partition_key, table_name, schema)

                    handler.write_parquet(rows, schema, ingested_at)

                    generated_files.add(handler.writer.where)

                batches_processed += 1
                rows_processed += len(batch)
            except Exception:
                failed_batch = batch_number
                raise

        elapsed = time.perf_counter() - start
        logger.info(
            "extraction ok | batches=%d rows=%d runtime=%.2fs",
            batches_processed,
            rows_processed,
            elapsed,
        )

        return generated_files
    except RuntimeError:
        logger.exception(
            "extraction failed at batch=%s | batches_ok=%d rows_ok=%d",
            failed_batch,
            batches_processed,
            rows_processed,
        )
        return set()  # INFO: return an empty set to indicate failure
    finally:
        pa_manager.close_all()
