CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- CUSTOMERS
-- ============================================================

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    city TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);


-- ============================================================
-- SELLERS
-- ============================================================

CREATE TABLE sellers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);


-- ============================================================
-- CATEGORIES
-- ============================================================

CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE
);


-- ============================================================
-- PRODUCTS
-- ============================================================

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    seller_id UUID NOT NULL
    REFERENCES sellers (id),

    category_id UUID NOT NULL
    REFERENCES categories (id),

    name TEXT NOT NULL,

    price NUMERIC(12, 2) NOT NULL,
    cost NUMERIC(12, 2) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT products_price_positive
    CHECK (price >= 0),

    CONSTRAINT products_cost_positive
    CHECK (cost >= 0)
);


-- ============================================================
-- COUPONS
-- ============================================================

CREATE TABLE coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code TEXT NOT NULL UNIQUE,

    discount_type TEXT NOT NULL,
    discount_value NUMERIC(12, 2) NOT NULL,

    minimum_order_amount NUMERIC(12, 2),

    starts_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT coupons_discount_type
    CHECK (discount_type IN ('percentage', 'fixed')),

    CONSTRAINT coupons_discount_positive
    CHECK (discount_value >= 0),

    CONSTRAINT coupons_dates_valid
    CHECK (expires_at > starts_at)
);


-- ============================================================
-- ORDERS
-- ============================================================

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    customer_id UUID NOT NULL
    REFERENCES customers (id),

    coupon_id UUID
    REFERENCES coupons (id),

    created_at TIMESTAMPTZ NOT NULL,

    status TEXT NOT NULL,

    shipping_fee NUMERIC(12, 2) NOT NULL DEFAULT 0,

    CONSTRAINT orders_status
    CHECK (
        status IN (
            'pending',
            'paid',
            'processing',
            'shipped',
            'delivered',
            'cancelled'
        )
    ),

    CONSTRAINT orders_shipping_fee_positive
    CHECK (shipping_fee >= 0)
);


-- ============================================================
-- ORDER ITEMS
-- ============================================================

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    order_id UUID NOT NULL
    REFERENCES orders (id)
    ON DELETE CASCADE,

    product_id UUID NOT NULL
    REFERENCES products (id),

    quantity INTEGER NOT NULL,

    unit_price NUMERIC(12, 2) NOT NULL,

    discount NUMERIC(12, 2) NOT NULL DEFAULT 0,

    CONSTRAINT order_items_quantity_positive
    CHECK (quantity > 0),

    CONSTRAINT order_items_price_positive
    CHECK (unit_price >= 0),

    CONSTRAINT order_items_discount_positive
    CHECK (discount >= 0)
);


-- ============================================================
-- PAYMENTS
-- ============================================================

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    order_id UUID NOT NULL
    REFERENCES orders (id)
    ON DELETE CASCADE,

    amount NUMERIC(12, 2) NOT NULL,

    payment_method TEXT NOT NULL,

    status TEXT NOT NULL,

    paid_at TIMESTAMPTZ,

    CONSTRAINT payments_amount_positive
    CHECK (amount >= 0),

    CONSTRAINT payments_method
    CHECK (
        payment_method IN (
            'credit_card',
            'debit_card',
            'gcash',
            'maya',
            'bank_transfer',
            'cod'
        )
    ),

    CONSTRAINT payments_status
    CHECK (
        status IN (
            'pending',
            'completed',
            'failed',
            'refunded'
        )
    )
);


-- ============================================================
-- SHIPMENTS
-- ============================================================

CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    order_id UUID NOT NULL UNIQUE
    REFERENCES orders (id)
    ON DELETE CASCADE,

    carrier TEXT NOT NULL,

    tracking_number TEXT NOT NULL UNIQUE,

    status TEXT NOT NULL,

    shipped_at TIMESTAMPTZ,

    delivered_at TIMESTAMPTZ,

    CONSTRAINT shipments_status
    CHECK (
        status IN (
            'pending',
            'shipped',
            'in_transit',
            'delivered',
            'lost'
        )
    ),

    CONSTRAINT shipments_dates_valid
    CHECK (
        delivered_at IS NULL
        OR shipped_at IS NULL
        OR delivered_at >= shipped_at
    )
);


-- ============================================================
-- RETURNS
-- ============================================================

CREATE TABLE returns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    order_item_id UUID NOT NULL
    REFERENCES order_items (id),

    quantity INTEGER NOT NULL,

    reason TEXT NOT NULL,

    status TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT returns_quantity_positive
    CHECK (quantity > 0),

    CONSTRAINT returns_status
    CHECK (
        status IN (
            'requested',
            'approved',
            'rejected',
            'completed'
        )
    )
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_orders_customer_id
ON orders (customer_id);

CREATE INDEX idx_orders_created_at
ON orders (created_at);

CREATE INDEX idx_orders_status
ON orders (status);

CREATE INDEX idx_order_items_order_id
ON order_items (order_id);

CREATE INDEX idx_order_items_product_id
ON order_items (product_id);

CREATE INDEX idx_products_seller_id
ON products (seller_id);

CREATE INDEX idx_products_category_id
ON products (category_id);

CREATE INDEX idx_payments_order_id
ON payments (order_id);

CREATE INDEX idx_shipments_order_id
ON shipments (order_id);

CREATE INDEX idx_returns_order_item_id
ON returns (order_item_id);
