
-- Source: staging.customers
-- Target: gold.dim_customer
-- Purpose: Customer dimension load

INSERT INTO gold.dim_customer (
    customer_key,
    customer_id,
    country
)
SELECT
    c.customer_id AS customer_key,
    c.customer_id,
    c.customer_name,
    c.country
FROM staging.customers c;
