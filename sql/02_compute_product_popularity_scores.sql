-- Compute Bayesian-style logarithmic product popularity score
-- Formula: popularity_score = LN(1 + total_delivered_orders + (total_favorites * 2))

WITH delivered_counts AS (
    SELECT 
        oi.product_id, 
        COUNT(DISTINCT o.id) AS total_delivered_orders
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.id
    WHERE o.status = 'Delivered'
    GROUP BY oi.product_id
),
favorite_counts AS (
    SELECT 
        product_id, 
        COUNT(*) AS total_favorites
    FROM favorites
    GROUP BY product_id
),
scores AS (
    SELECT 
        p.id AS product_id,
        ROUND(
            LN(
                1.0 + 
                COALESCE(d.total_delivered_orders, 0) + 
                (COALESCE(f.total_favorites, 0) * 2.0)
            )::numeric, 
            4
        ) AS computed_score
    FROM products p
    LEFT JOIN delivered_counts d ON p.id = d.product_id
    LEFT JOIN favorite_counts f ON p.id = f.product_id
)
UPDATE products p
SET popularity_score = s.computed_score
FROM scores s
WHERE p.id = s.product_id;
