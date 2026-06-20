# Olist Project - PostgreSQL (SQL) Queries

This document contains the complete set of PostgreSQL queries used in the project to run against the relational database schemas.

---

## 📂 Query 1: Sales Representative (SR) Performance (HR Analysis)
Find the top 5 sales representatives (SDR/SR) who onboarded sellers with the highest average review scores (for reps with more than 10 reviews).

```sql
SELECT 
    closed_deals.sr_id,
    COUNT(DISTINCT reviews.review_id) AS total_reviews,
    ROUND(AVG(reviews.review_score), 2) AS avg_review_score
FROM 
    olist_closed_deals_dataset closed_deals
JOIN 
    olist_order_items_dataset order_items ON closed_deals.seller_id = order_items.seller_id
JOIN 
    olist_order_reviews_dataset reviews ON order_items.order_id = reviews.order_id
GROUP BY 
    closed_deals.sr_id
HAVING 
    COUNT(DISTINCT reviews.review_id) > 10
ORDER BY 
    avg_review_score DESC
LIMIT 5;
```

---

## 📂 Query 2: Product Categories with High Negative Reviews
Identify the top 5 product categories with the highest percentage of negative reviews (scores of 1 or 2), alongside the average price of products in those categories (for categories with over 50 reviews).

```sql
SELECT 
    products.product_category_name AS category_portuguese,
    category_translation.product_category_name_english AS category_english,
    COUNT(reviews.review_id) AS total_reviews,
    SUM(CASE WHEN reviews.review_score IN (1, 2) THEN 1 ELSE 0 END) AS negative_reviews,
    ROUND(((SUM(CASE WHEN reviews.review_score IN (1, 2) THEN 1 ELSE 0 END) * 100.0) / COUNT(reviews.review_id))::numeric, 2) AS negative_reviews_percentage,
    ROUND(AVG(order_items.price)::numeric, 2) AS avg_price
FROM 
    olist_products_dataset products
JOIN 
    product_category_name_translation category_translation ON products.product_category_name = category_translation.product_category_name
JOIN 
    olist_order_items_dataset order_items ON products.product_id = order_items.product_id
JOIN 
    olist_order_reviews_dataset reviews ON order_items.order_id = reviews.order_id
GROUP BY 
    products.product_category_name, 
    category_translation.product_category_name_english
HAVING 
    COUNT(reviews.review_id) > 50
ORDER BY 
    negative_reviews_percentage DESC
LIMIT 5;
```

---

## 📂 Query 3: ROI of Marketing Funnel Channels
Find the total revenue generated and the count of unique recruited sellers for each marketing channel lead origin.

```sql
SELECT 
    marketing_qualified_leads.origin AS marketing_origin,
    COUNT(DISTINCT closed_deals.seller_id) AS recruited_sellers,
    ROUND(SUM(order_items.price)::numeric, 2) AS total_revenue_generated
FROM 
    olist_marketing_qualified_leads_dataset marketing_qualified_leads
JOIN 
    olist_closed_deals_dataset closed_deals ON marketing_qualified_leads.mql_id = closed_deals.mql_id
JOIN 
    olist_order_items_dataset order_items ON closed_deals.seller_id = order_items.seller_id
WHERE 
    marketing_qualified_leads.origin IS NOT NULL
GROUP BY 
    marketing_qualified_leads.origin
ORDER BY 
    total_revenue_generated DESC;
```

---

## 📂 Query 4: Impact of Shipping Delays on Review Scores
Compare average review scores for orders that were delivered on-time or early vs. orders delivered late.

```sql
SELECT 
    CASE 
        WHEN orders.order_delivered_customer_date > orders.order_estimated_delivery_date THEN 'Late Delivery'
        ELSE 'On Time or Early'
    END AS delivery_status,
    COUNT(DISTINCT orders.order_id) AS total_orders,
    ROUND(AVG(reviews.review_score)::numeric, 2) AS avg_review_score
FROM 
    olist_orders_dataset orders
JOIN 
    olist_order_reviews_dataset reviews ON orders.order_id = reviews.order_id
WHERE 
    orders.order_delivered_customer_date IS NOT NULL 
    AND orders.order_estimated_delivery_date IS NOT NULL
GROUP BY 
    CASE 
        WHEN orders.order_delivered_customer_date > orders.order_estimated_delivery_date THEN 'Late Delivery'
        ELSE 'On Time or Early'
    END;
```

---

## 📂 Query 5: Geographical Shipping Cost Analysis
Identify states in Brazil where the total shipping freight cost exceeds 30% of the total product value.

```sql
SELECT 
    customers.customer_state,
    COUNT(DISTINCT orders.order_id) AS total_orders,
    ROUND(SUM(order_items.price)::numeric, 2) AS total_revenue,
    ROUND(((SUM(order_items.freight_value) * 100.0) / SUM(order_items.price))::numeric, 2) AS freight_to_price_percentage
FROM 
    olist_orders_dataset orders
JOIN 
    olist_customers_dataset customers ON orders.customer_id = customers.customer_id
JOIN 
    olist_order_items_dataset order_items ON orders.order_id = order_items.order_id
GROUP BY 
    customers.customer_state
HAVING 
    (SUM(order_items.freight_value) / SUM(order_items.price)) > 0.30
ORDER BY 
    freight_to_price_percentage DESC;
```
