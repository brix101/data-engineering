import duckdb

conn = duckdb.connect()

# INFO: Total Orders per Status
# result = conn.execute("""
#     SELECT
#         status,
#         COUNT(*) AS order_count
#     FROM read_parquet('data/parquet/orders/**/*.parquet')
#     GROUP BY status
#     ORDER BY order_count DESC
#     """).fetchall()

# INFO: Total Orders per Month
# result = conn.execute("""
#     SELECT
#         date_trunc('month', created_at) AS month,
#         COUNT(*) AS order_count
#     FROM read_parquet('data/parquet/orders/**/*.parquet')
#     GROUP BY month
#     ORDER BY order_count DESC
#     """).fetchall()

# INFO: Total Revenue
# result = conn.execute("""
#     SELECT
#         SUM((quantity * unit_price) - discount) AS total_revenue
#     FROM read_parquet('data/parquet/order_items/**/*.parquet')
#     """).fetchall()

# INFO: Total Revenue per Order Status
# result = conn.execute("""
#     SELECT
#         o.status,
#         SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue
#     FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#     JOIN read_parquet('data/parquet/order_items/**/*.parquet') AS oi
#     ON o.id = oi.order_id
#     WHERE o.status NOT IN ('cancelled', 'pending')
#     GROUP BY o.status
#     ORDER BY total_revenue DESC
#     """).fetchall()

# INFO: Total Revenue per Month
# result = conn.execute("""
#     SELECT
#         date_trunc('month', o.created_at) AS month,
#         SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue
#     FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#     JOIN read_parquet('data/parquet/order_items/**/*.parquet') AS oi
#     ON o.id = oi.order_id
#     WHERE o.status NOT IN ('cancelled', 'pending')
#     GROUP BY month
#     ORDER BY month DESC
#     """).fetchall()

# INFO: AVG Order Value per Month
# result = conn.execute("""
#     SELECT
#         date_trunc('month', o.created_at) AS month,
#         COUNT(DISTINCT o.id) AS order_count,
#         SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue,
#         SUM((oi.quantity * oi.unit_price) - oi.discount) / COUNT(DISTINCT o.id) AS average_order_value
#     FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#     JOIN read_parquet('data/parquet/order_items/**/*.parquet') AS oi
#     ON o.id = oi.order_id
#     WHERE o.status NOT IN ('cancelled', 'pending')
#     GROUP BY month
#     ORDER BY month DESC
#     """).fetchall()

# # INFO: Top Products
# result = conn.execute("""
#     SELECT
#         p.name AS product_name,
#         SUM(oi.quantity) AS total_quantity_sold,
#         SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue
#     FROM read_parquet('data/parquet/order_items/**/*.parquet') AS oi
#         JOIN read_parquet('data/parquet/products/**/*.parquet') AS p ON oi.product_id = p.id
#         JOIN read_parquet('data/parquet/orders/**/*.parquet') AS o ON oi.order_id = o.id
#     WHERE o.status NOT IN ('cancelled', 'pending')
#     GROUP BY p.id, p.name
#     ORDER BY total_revenue DESC
#     LIMIT 10
#     """).fetchall()

# INFO: Top Categories
# result = conn.execute("""
#     SELECT
#         c.name AS category_name,
#         SUM(oi.quantity) AS total_quantity_sold,
#         SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue
#     FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#         JOIN read_parquet('data/parquet/order_items/**/*.parquet') AS oi ON o.id = oi.order_id
#         JOIN read_parquet('data/parquet/products/**/*.parquet') AS p ON oi.product_id = p.id
#         JOIN read_parquet('data/parquet/categories/**/*.parquet') AS c ON p.category_id = c.id
#     WHERE o.status NOT IN ('cancelled', 'pending')
#     GROUP BY c.id, c.name
#     ORDER BY total_revenue DESC
#     LIMIT 10
#     """).fetchall()

# INFO: Top Customers
# result = conn.execute("""
#     SELECT
#         c.id as customer_id,
#         CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
#         COUNT(DISTINCT o.id) as order_count,
#         SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue
#     FROM read_parquet('data/parquet/customers/**/*.parquet') AS c
#         JOIN read_parquet('data/parquet/orders/**/*.parquet') AS o ON o.customer_id = c.id
#         JOIN read_parquet('data/parquet/order_items/**/*.parquet') AS oi ON oi.order_id = o.id
#     WHERE o.status NOT IN ('cancelled', 'pending')
#     GROUP BY c.id, c.first_name, c.last_name
#     ORDER BY total_revenue DESC
#     LIMIT 10
#     """).fetchall()


# INFO: Repeat customers
# INFO: CTE Example - Customer Type Classification
# INFO: Classify customers as "repeat" or "one_time" based on their order history
# result = conn.execute("""
#     with customer_orders as (
#         SELECT
#             o.customer_id,
#             COUNT(DISTINCT o.id) as order_count
#         FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#         WHERE o.status NOT IN ('cancelled', 'pending')
#         GROUP BY o.customer_id
#     )
#
#     SELECT
#         CASE
#             WHEN order_count >= 2 THEN 'repeat'
#             ELSE 'one_time'
#         END AS customer_type,
#         COUNT(*) AS customer_count
#     FROM customer_orders
#     GROUP BY customer_type
#     """).fetchall()

# INFO: Part 1 — Customer Purchase Frequency
# result = conn.execute("""
#     with customer_orders as (
#         SELECT
#             o.customer_id,
#             COUNT(DISTINCT o.id) as order_count
#         FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#         WHERE o.status NOT IN ('cancelled', 'pending')
#         GROUP BY o.customer_id
#     )
#
#     SELECT
#         AVG(order_count) AS average_orders_per_customer,
#     FROM customer_orders
#     """).fetchall()

# INFO: Part 2 — Top 10 Customers by Number of Orders
# result = conn.execute("""
#     with customer_orders as (
#         SELECT
#             o.customer_id,
#             COUNT(DISTINCT o.id) as order_count
#         FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#         WHERE o.status NOT IN ('cancelled', 'pending')
#         GROUP BY o.customer_id
#     )
#
#     SELECT
#         co.customer_id,
#         CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
#         co.order_count
#     FROM customer_orders as co
#         JOIN read_parquet('data/parquet/customers/**/*.parquet') AS c ON co.customer_id = c.id
#     ORDER BY co.order_count DESC
#     LIMIT 10
#     """).fetchall()

# INFO: Part 3 — Top 10 Customers by Revenue
# result = conn.execute("""
#     with customer_orders as (
#         SELECT
#             o.customer_id,
#             COUNT(DISTINCT o.id) as order_count,
#             SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue
#         FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#             JOIN read_parquet('data/parquet/order_items/**/*.parquet') AS oi ON oi.order_id = o.id
#         WHERE o.status NOT IN ('cancelled', 'pending')
#         GROUP BY o.customer_id
#     )
#
#     SELECT
#         co.customer_id,
#         CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
#         co.order_count,
#         co.total_revenue
#     FROM customer_orders as co
#         JOIN read_parquet('data/parquet/customers/**/*.parquet') AS c ON co.customer_id = c.id
#     ORDER BY co.total_revenue DESC
#     LIMIT 10
#     """).fetchall()

# INFO: Part 4 — Repeat Customer Revenue
# result = conn.execute("""
#     with customer_orders as (
#         SELECT
#             o.customer_id,
#             COUNT(DISTINCT o.id) as order_count,
#             SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue
#         FROM read_parquet('data/parquet/orders/**/*.parquet') AS o
#             JOIN read_parquet('data/parquet/order_items/**/*.parquet') AS oi ON oi.order_id = o.id
#         WHERE o.status NOT IN ('cancelled', 'pending')
#         GROUP BY o.customer_id
#     )
#
#     SELECT
#         CASE
#             WHEN order_count >= 2 THEN 'repeat'
#             ELSE 'one_time'
#         END AS customer_type,
#         COUNT(*) AS customer_count,
#         SUM(total_revenue) AS total_revenue
#     FROM customer_orders
#     GROUP BY customer_type
#     """).fetchall()

# INFO: Part 5 — Returns Analytics
# INFO: 5A — Total Returned Items
# result = conn.execute("""
#     SELECT
#         SUM(quantity) AS total_items_returned
#     FROM read_parquet('data/parquet/returns/**/*.parquet')
#     """).fetchall()

# INFO: 5B — Returns by Reason
# result = conn.execute("""
#     SELECT
#         reason,
#         COUNT(*) AS return_count,
#         SUM(quantity) AS returned_quantity
#     FROM read_parquet('data/parquet/returns/**/*.parquet')
#     GROUP BY reason
#     """).fetchall()

# INFO: 5C — Return Rate
# INFO: What percentage of sold item quantity was returned?
# NOTE: Aggregate each side independently to avoid duplicate counting.
#       If an order_item has N return rows, a direct JOIN would
#       count oi.quantity N times on the "sold" side.
# result = conn.execute("""
#     WITH sold AS (
#         SELECT SUM(quantity) AS total_sold_quantity
#         FROM read_parquet('data/parquet/order_items/**/*.parquet')
#     ),
#     returned AS (
#         SELECT SUM(quantity) AS total_returned_quantity
#         FROM read_parquet('data/parquet/returns/**/*.parquet')
#     )
#
#     SELECT
#         s.total_sold_quantity,
#         r.total_returned_quantity,
#         ROUND((r.total_returned_quantity * 100.0) / s.total_sold_quantity, 2) AS return_rate_pct
#     FROM sold AS s, returned AS r
#     """).fetchall()

# Part 6 — Gross Profit
result = conn.execute("""
    SELECT
        p.id AS product_id,
        p.name AS product_name,
        SUM(oi.quantity) AS total_quantity_sold,
        SUM((oi.quantity * oi.unit_price) - oi.discount) AS total_revenue,
        p.cost * SUM(oi.quantity) AS total_cost,
        SUM((oi.quantity * oi.unit_price) - oi.discount) - (p.cost * SUM(oi.quantity)) AS gross_profit
    FROM read_parquet('data/parquet/order_items/**/*.parquet') AS oi
        JOIN read_parquet('data/parquet/products/**/*.parquet') AS p ON oi.product_id = p.id
        JOIN read_parquet('data/parquet/orders/**/*.parquet') AS o ON oi.order_id = o.id
    WHERE o.status NOT IN ('cancelled', 'pending')
    GROUP BY p.id, p.name, p.cost
    ORDER BY gross_profit DESC
    LIMIT 10
    """).fetchall()

print(result)

conn.close()
