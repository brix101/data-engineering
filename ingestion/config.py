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
