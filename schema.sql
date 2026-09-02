CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    city TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE sellers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID NOT NULL REFERENCES sellers (id),
    category_id UUID NOT NULL REFERENCES categories (id),
    name TEXT NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    cost NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers (id),
    created_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    shipping_fee NUMERIC(12, 2) NOT NULL DEFAULT 0
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders (id),
    product_id UUID NOT NULL REFERENCES products (id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    discount NUMERIC(12, 2) NOT NULL DEFAULT 0
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders (id),
    amount NUMERIC(12, 2) NOT NULL,
    status TEXT NOT NULL,
    paid_at TIMESTAMPTZ
);

CREATE TABLE returns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_item_id UUID NOT NULL REFERENCES order_items (id),
    quantity INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
