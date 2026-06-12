/* ==============================================================================
   Olist E-Commerce & Marketing Funnel Database Schema - VERSION 2.0
   Description: Comprehensive schema including 11 tables. 
                Added Geolocation support and cross-dataset integrity.
   ============================================================================== */

-- ==========================================
-- PHASE 0: Cleanup (Optional - Run if tables exist)
-- ==========================================
--DROP TABLE IF EXISTS reviews, payments, order_items, closed_deals, orders, products, customers, sellers, category_translation, marketing_qualified_leads, geolocation CASCADE;

-- ==========================================
-- PHASE 1: Base Tables (No Foreign Keys)
-- ==========================================

-- 1. Geolocation Table: Centralized location data for Brazil.
-- Note: This is the parent table for addresses in this dataset.
CREATE TABLE geolocation (
    geolocation_zip_code_prefix VARCHAR(10) PRIMARY KEY,
    geolocation_lat DECIMAL(10, 8),
    geolocation_lng DECIMAL(11, 8),
    geolocation_city VARCHAR(100),
    geolocation_state VARCHAR(2)
);

-- 2. Category Translation Table: Maps Portuguese category names to English.
CREATE TABLE category_translation (
    product_category_name VARCHAR(100) PRIMARY KEY,
    product_category_name_english VARCHAR(100)
);

-- 3. Marketing Qualified Leads (MQL) Table: Stores top-of-funnel marketing leads.
CREATE TABLE marketing_qualified_leads (
    mql_id VARCHAR(50) PRIMARY KEY,
    first_contact_date DATE,
    landing_page_id VARCHAR(50),
    origin VARCHAR(50)
);

-- ==========================================
-- PHASE 2: Tables with Dependencies (Foreign Keys)
-- ==========================================

-- 4. Customers Table: Links to geolocation via zip_code.
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100),
    customer_state VARCHAR(2),
    FOREIGN KEY (customer_zip_code_prefix) REFERENCES geolocation(geolocation_zip_code_prefix)
);

-- 5. Sellers Table: Links to geolocation via zip_code.
CREATE TABLE sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(10),
    seller_city VARCHAR(100),
    seller_state VARCHAR(2),
    FOREIGN KEY (seller_zip_code_prefix) REFERENCES geolocation(geolocation_zip_code_prefix)
);

-- 6. Products Table: Linked to category translation.
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g INT,
    product_length_cm INT,
    product_height_cm INT,
    product_width_cm INT,
    FOREIGN KEY (product_category_name) REFERENCES category_translation(product_category_name)
);

-- 7. Orders Table: Linked to customers.
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    order_status VARCHAR(20),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 8. Closed Deals Table: Bridges marketing leads and sellers.
CREATE TABLE closed_deals (
    mql_id VARCHAR(50) PRIMARY KEY,
    seller_id VARCHAR(50),
    sdr_id VARCHAR(50),
    sr_id VARCHAR(50),
    won_date TIMESTAMP,
    business_segment VARCHAR(50),
    lead_type VARCHAR(50),
    lead_behaviour_profile VARCHAR(50),
    has_company BOOLEAN,
    has_gtin BOOLEAN,
    average_stock VARCHAR(20),
    business_type VARCHAR(50),
    declared_monthly_revenue DECIMAL(15, 2),
    FOREIGN KEY (mql_id) REFERENCES marketing_qualified_leads(mql_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

-- ==========================================
-- PHASE 3: Transactional Tables (Composite Keys)
-- ==========================================

-- 9. Order Items Table: Links orders, products, and sellers.
CREATE TABLE order_items (
    order_id VARCHAR(50),
    order_item_id INT,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    shipping_limit_date TIMESTAMP,
    price DECIMAL(10, 2),
    freight_value DECIMAL(10, 2),
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

-- 10. Payments Table: Payment details per order.
CREATE TABLE payments (
    order_id VARCHAR(50),
    payment_sequential INT,
    payment_type VARCHAR(20),
    payment_installments INT,
    payment_value DECIMAL(10, 2),
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- 11. Reviews Table: Customer feedback per order.
CREATE TABLE reviews (
    review_id VARCHAR(50),
    order_id VARCHAR(50),
    review_score INT,
    review_comment_title VARCHAR(255),
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    PRIMARY KEY (review_id, order_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
