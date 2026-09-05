import logging

from ingestion.ingestion import ingest_table
from ingestion.storage import (
    ensure_bucket,
    get_s3_client,
    object_exists,
    upload_file,
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


if __name__ == "__main__":
    bucket_name = "ecommerce-data"
    client = get_s3_client()
    ensure_bucket(client, bucket_name)

    for table_name, config in TABLE_CONFIG.items():
        if table_name != "orders":  # Skip orders table for now
            continue

        generated_files = ingest_table(
            table_name,
            config["primary_key"],
            config["required_columns"],
            config["partition_column"],
        )

        for file_path in generated_files:
            relative_path = file_path.relative_to("data/parquet")
            object_name = relative_path.as_posix()

            upload_file(client, bucket_name, file_path, object_name)

            if object_exists(client, bucket_name, object_name):
                logger.info("removing '%s'", file_path)
                file_path.unlink()
