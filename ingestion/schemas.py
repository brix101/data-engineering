import pyarrow as pa

# Parquet schemas per source table, mirroring schema.sql.
#
# Type mapping:
#   UUID          -> pa.uuid()                 (extension type; 16-byte fixed
#                                                binary storage. Pass `UUID.bytes`
#                                                at ingest time.)
#   TEXT          -> pa.string()
#   INTEGER       -> pa.int32()                (Postgres INTEGER is 4-byte)
#   NUMERIC(p, s) -> pa.decimal128(p, s)
#   TIMESTAMPTZ   -> pa.timestamp("us")        (naive; convert tz-aware datetimes
#                                                to UTC-naive at ingest time)
#
# Every schema ends with an "ingested_at" column stamped by the runner.

customers_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("email", pa.string()),
        ("first_name", pa.string()),
        ("last_name", pa.string()),
        ("city", pa.string()),
        ("created_at", pa.timestamp("us")),
        ("ingested_at", pa.timestamp("us")),
    ]
)

sellers_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("name", pa.string()),
        ("created_at", pa.timestamp("us")),
        ("ingested_at", pa.timestamp("us")),
    ]
)

categories_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("name", pa.string()),
        ("ingested_at", pa.timestamp("us")),
    ]
)

products_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("seller_id", pa.uuid()),
        ("category_id", pa.uuid()),
        ("name", pa.string()),
        ("price", pa.decimal128(12, 2)),
        ("cost", pa.decimal128(12, 2)),
        ("created_at", pa.timestamp("us")),
        ("ingested_at", pa.timestamp("us")),
    ]
)

coupons_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("code", pa.string()),
        ("discount_type", pa.string()),
        ("discount_value", pa.decimal128(12, 2)),
        ("minimum_order_amount", pa.decimal128(12, 2)),
        ("starts_at", pa.timestamp("us")),
        ("expires_at", pa.timestamp("us")),
        ("ingested_at", pa.timestamp("us")),
    ]
)

orders_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("customer_id", pa.uuid()),
        ("coupon_id", pa.uuid()),
        ("created_at", pa.timestamp("us")),
        ("status", pa.string()),
        ("shipping_fee", pa.decimal128(12, 2)),
        ("ingested_at", pa.timestamp("us")),
    ]
)

order_items_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("order_id", pa.uuid()),
        ("product_id", pa.uuid()),
        ("quantity", pa.int32()),
        ("unit_price", pa.decimal128(12, 2)),
        ("discount", pa.decimal128(12, 2)),
        ("ingested_at", pa.timestamp("us")),
    ]
)

payments_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("order_id", pa.uuid()),
        ("amount", pa.decimal128(12, 2)),
        ("payment_method", pa.string()),
        ("status", pa.string()),
        ("paid_at", pa.timestamp("us")),
        ("ingested_at", pa.timestamp("us")),
    ]
)

shipments_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("order_id", pa.uuid()),
        ("carrier", pa.string()),
        ("tracking_number", pa.string()),
        ("status", pa.string()),
        ("shipped_at", pa.timestamp("us")),
        ("delivered_at", pa.timestamp("us")),
        ("ingested_at", pa.timestamp("us")),
    ]
)

returns_schema = pa.schema(
    [
        ("id", pa.uuid()),
        ("order_item_id", pa.uuid()),
        ("quantity", pa.int32()),
        ("reason", pa.string()),
        ("status", pa.string()),
        ("created_at", pa.timestamp("us")),
        ("ingested_at", pa.timestamp("us")),
    ]
)


TABLE_SCHEMAS: dict[str, pa.Schema] = {
    "customers": customers_schema,
    "sellers": sellers_schema,
    "categories": categories_schema,
    "products": products_schema,
    "coupons": coupons_schema,
    "orders": orders_schema,
    "order_items": order_items_schema,
    "payments": payments_schema,
    "shipments": shipments_schema,
    "returns": returns_schema,
}
