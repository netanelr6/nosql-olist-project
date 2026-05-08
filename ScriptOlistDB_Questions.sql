
------------------------------------------------------------
-----------------------Questions  1 ------------------------
SELECT 
    closed_deals.sr_id,
    COUNT(DISTINCT reviews.review_id) AS total_reviews,
    ROUND(AVG(reviews.review_score), 2) AS avg_review_score
FROM 
    closed_deals
JOIN 
    order_items ON closed_deals.seller_id = order_items.seller_id
JOIN 
    reviews ON order_items.order_id = reviews.order_id
GROUP BY 
    closed_deals.sr_id
HAVING 
    COUNT(DISTINCT reviews.review_id) > 10
ORDER BY 
    avg_review_score DESC
LIMIT 5



------------------------------------------------------------
-----------------------Questions  2 ------------------------
SELECT 
    products.product_category_name AS category_portuguese,
    category_translation.product_category_name_english AS category_english,
    COUNT(reviews.review_id) AS total_reviews,
    SUM(CASE WHEN reviews.review_score IN (1, 2) THEN 1 ELSE 0 END) AS negative_reviews,
    ROUND((SUM(CASE WHEN reviews.review_score IN (1, 2) THEN 1 ELSE 0 END) * 100.0) / COUNT(reviews.review_id), 2) AS negative_reviews_percentage,
    ROUND(AVG(order_items.price), 2) AS avg_price
FROM 
    products
JOIN 
    category_translation ON products.product_category_name = category_translation.product_category_name
JOIN 
    order_items ON products.product_id = order_items.product_id
JOIN 
    reviews ON order_items.order_id = reviews.order_id
GROUP BY 
    products.product_category_name, 
    category_translation.product_category_name_english
HAVING 
    COUNT(reviews.review_id) > 50
ORDER BY 
    negative_reviews_percentage DESC
LIMIT 5;


------------------------------------------------------------
-----------------------Questions  3 ------------------------

SELECT 
    marketing_qualified_leads.origin AS marketing_origin,
    COUNT(DISTINCT closed_deals.seller_id) AS recruited_sellers,
    ROUND(SUM(order_items.price), 2) AS total_revenue_generated
FROM 
    marketing_qualified_leads
JOIN 
    closed_deals ON marketing_qualified_leads.mql_id = closed_deals.mql_id
JOIN 
    order_items ON closed_deals.seller_id = order_items.seller_id
WHERE 
    marketing_qualified_leads.origin IS NOT NULL
GROUP BY 
    marketing_qualified_leads.origin
ORDER BY 
    total_revenue_generated DESC;

------------------------------------------------------------
-----------------------Questions  4 ------------------------

SELECT 
    CASE 
        WHEN orders.order_delivered_customer_date > orders.order_estimated_delivery_date THEN 'Late Delivery'
        ELSE 'On Time or Early'
    END AS delivery_status,
    COUNT(DISTINCT orders.order_id) AS total_orders,
    ROUND(AVG(reviews.review_score), 2) AS avg_review_score
FROM 
    orders
JOIN 
    reviews ON orders.order_id = reviews.order_id
WHERE 
    orders.order_delivered_customer_date IS NOT NULL 
    AND orders.order_estimated_delivery_date IS NOT NULL
GROUP BY 
    CASE 
        WHEN orders.order_delivered_customer_date > orders.order_estimated_delivery_date THEN 'Late Delivery'
        ELSE 'On Time or Early'
    END;

------------------------------------------------------------
-----------------------Questions  5 ------------------------

SELECT 
    customers.customer_state,
    COUNT(DISTINCT orders.order_id) AS total_orders,
    ROUND(SUM(order_items.price), 2) AS total_revenue,
    ROUND((SUM(order_items.freight_value) * 100.0) / SUM(order_items.price), 2) AS freight_to_price_percentage
FROM 
    orders
JOIN 
    customers ON orders.customer_id = customers.customer_id
JOIN 
    order_items ON orders.order_id = order_items.order_id
GROUP BY 
    customers.customer_state
HAVING 
    (SUM(order_items.freight_value) / SUM(order_items.price)) > 0.30
ORDER BY 
    freight_to_price_percentage DESC;




------------------------------------------------------------
--------------------------END-------------------------------
------------------------------------------------------------