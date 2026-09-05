import argparse
import logging
import sys

from ingestion.config import TABLE_CONFIG
from ingestion.ingestion import ingest_table
from ingestion.storage import StorageClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


storage = StorageClient()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest a table and optionally upload/delete the generated parquet files.",
    )
    parser.add_argument(
        "-t",
        "--table",
        required=True,
        choices=sorted(TABLE_CONFIG.keys()),
        help="Table name to ingest (must exist in TABLE_CONFIG).",
    )
    parser.add_argument(
        "-u",
        "--upload",
        action="store_true",
        help="Upload generated parquet files to object storage.",
    )
    parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Delete local parquet files after a successful upload. Requires --upload.",
    )

    args = parser.parse_args()

    if args.delete and not args.upload:
        parser.error("--delete/-d requires --upload/-u (won't delete files that weren't uploaded).")

    return args


if __name__ == "__main__":
    args = parse_args()

    bucket_name = "ecommerce-data"
    storage.ensure_bucket(bucket_name)

    table_name = args.table
    config = TABLE_CONFIG[table_name]

    if not config:
        logger.error("No configuration found for table '%s'", table_name)
        sys.exit(1)

    generated_files = ingest_table(table_name, config)

    if args.upload:
        for file_path in generated_files:
            relative_path = file_path.relative_to("data/parquet")
            object_name = relative_path.as_posix()

            storage.upload_file(bucket_name, file_path, object_name)

            if args.delete and storage.object_exists(bucket_name, object_name):
                logger.info("removing '%s'", file_path)
                file_path.unlink()
