
-- Source: staging.orders
-- Target: gold.fact_orders
-- Purpose: Order fact load

INSERT INTO gold.fact_orders (
    order_key,
    order_id,
    customer_key,
    order_date,
    order_total
)
SELECT
    o.order_id AS order_key,
    o.order_id,
    d.customer_key,
    o.order_date,
    o.amount
FROM staging.orders o
JOIN gold.dim_customer d
    ON o.customer_id = d.customer_id;
