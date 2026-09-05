import logging

from ingestion.config import TABLE_CONFIG
from ingestion.ingestion import ingest_table
from ingestion.storage import StorageClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


storage = StorageClient()


if __name__ == "__main__":
    bucket_name = "ecommerce-data"
    storage.ensure_bucket(bucket_name)

    for table_name, config in TABLE_CONFIG.items():
        if table_name != "orders":  # Skip orders table for now
            continue

        generated_files = ingest_table(table_name, config)

        # for file_path in generated_files:
        #     relative_path = file_path.relative_to("data/parquet")
        #     object_name = relative_path.as_posix()
        #
        #     storage.upload_file(bucket_name, file_path, object_name)
        #
        #     if storage.object_exists(bucket_name, object_name):
        #         logger.info("removing '%s'", file_path)
        #         file_path.unlink()
