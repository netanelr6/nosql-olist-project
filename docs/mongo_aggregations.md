# SQL to MongoDB Aggregation Translation (Task 4)

This document provides the MongoDB Aggregation Pipeline translations for the five complex SQL queries from Homework 1. For each query, we explain the design considerations of the relational model vs. the document model, and present the aggregation pipeline in MongoDB shell format.

---

## Query 1: Sales Agents Rating by Supplier Quality

### Description & Intent
Find the top 5 sales representatives (`sr_id`) ranked by the average review score of the products sold by the sellers they onboarded. We filter for sales reps who have at least 10 reviews.

### Relational Join Path (SQL)
`closed_deals` $\rightarrow$ `order_items` $\rightarrow$ `reviews`

### MongoDB Strategy
1. **Source Collection**: `reviews`
2. **Step-by-step**:
   - `$unwind` the `order_id` references array.
   - `$lookup` the corresponding `orders` documents.
   - `$unwind` the matched `orders` and then the nested `items` array.
   - `$lookup` the corresponding `sellers` documents to find onboarding details (which contain `sr_id`).
   - Filter for sellers that actually have an associated `sr_id`.
   - Perform a two-stage group:
     - Group 1: Group by `sr_id` and `review_id` to deduplicate review counts (handling orders containing multiple items).
     - Group 2: Group by `sr_id` to compute the count of unique reviews and calculate the average score.
   - Match reps with $> 10$ reviews.
   - Sort descending by average score and limit to the top 5.

### MongoDB Aggregation Pipeline
```javascript
db.reviews.aggregate([
  // Step 1: Unwind order references from the reviews collection
  { "$unwind": "$order_id" },
  
  // Step 2: Join with the orders collection
  {
    "$lookup": {
      "from": "orders",
      "localField": "order_id",
      "foreignField": "_id",
      "as": "order_details"
    }
  },
  { "$unwind": "$order_details" },
  
  // Step 3: Unwind items within each order to locate the seller
  { "$unwind": "$order_details.items" },
  
  // Step 4: Join with the sellers collection to extract sales representative (sr_id)
  {
    "$lookup": {
      "from": "sellers",
      "localField": "order_details.items.seller_id",
      "foreignField": "_id",
      "as": "seller_details"
    }
  },
  { "$unwind": "$seller_details" },
  
  // Step 5: Filter out sellers without a sales rep
  {
    "$match": {
      "seller_details.onboarding_details.sr_id": { "$exists": true, "$ne": null }
    }
  },
  
  // Step 6: First-stage grouping to deduplicate reviews (by rep and review ID)
  {
    "$group": {
      "_id": {
        "sr_id": "$seller_details.onboarding_details.sr_id",
        "review_id": "$_id"
      },
      "review_score": { "$first": "$review_score" }
    }
  },
  
  // Step 7: Second-stage grouping per sales rep
  {
    "$group": {
      "_id": "$_id.sr_id",
      "total_reviews": { "$sum": 1 },
      "avg_review_score": { "$avg": "$review_score" }
    }
  },
  
  // Step 8: Apply HAVING filter (total reviews > 10)
  {
    "$match": {
      "total_reviews": { "$gt": 10 }
    }
  },
  
  // Step 9: Sort and limit
  { "$sort": { "avg_review_score": -1 } },
  { "$limit": 5 },
  
  // Step 10: Project clean outputs
  {
    "$project": {
      "_id": 0,
      "sr_id": "$_id",
      "total_reviews": 1,
      "avg_review_score": { "$round": ["$avg_review_score", 2] }
    }
  }
])
```

---

## Query 2: Product Categories with Negative Reviews

### Description & Intent
Identify the top 5 product categories (in both Portuguese and English) that have the highest percentage of negative reviews (ratings of 1 or 2). We restrict results to categories with more than 50 total reviews.

### Relational Join Path (SQL)
`products` $\rightarrow$ `category_translation` $\rightarrow$ `order_items` $\rightarrow$ `reviews`

### MongoDB Strategy
1. **Source Collection**: `reviews` (or `orders`, but `reviews` is cleaner for grouping scores).
2. **Step-by-step**:
   - `$unwind` the `order_id` array from the review document.
   - `$lookup` the `orders` collection to find the items associated with that order.
   - `$unwind` the order's `items`.
   - `$lookup` the `products` collection using `item.product_id` to get category details (translated category names are pre-embedded in `products` in our design).
   - `$unwind` the matched product.
   - Group by category name (Portuguese and English) and aggregate:
     - Total review count.
     - Negative review count (score is 1 or 2) using a conditional `$cond`.
     - Average product price.
   - Match categories with $> 50$ total reviews.
   - Project and calculate negative percentage = `(negative_reviews / total_reviews) * 100`.
   - Sort by negative percentage descending and limit to top 5.

### MongoDB Aggregation Pipeline
```javascript
db.reviews.aggregate([
  // Step 1: Unwind order references
  { "$unwind": "$order_id" },
  
  // Step 2: Join with orders
  {
    "$lookup": {
      "from": "orders",
      "localField": "order_id",
      "foreignField": "_id",
      "as": "order_details"
    }
  },
  { "$unwind": "$order_details" },
  { "$unwind": "$order_details.items" },
  
  // Step 3: Join with products to get pre-translated category names
  {
    "$lookup": {
      "from": "products",
      "localField": "order_details.items.product_id",
      "foreignField": "_id",
      "as": "product_details"
    }
  },
  { "$unwind": "$product_details" },
  
  // Step 4: Group by category
  {
    "$group": {
      "_id": {
        "category_portuguese": "$product_details.product_category_name",
        "category_english": "$product_details.product_category_name_english"
      },
      "total_reviews": { "$sum": 1 },
      "negative_reviews": {
        "$sum": {
          "$cond": [
            { "$in": ["$review_score", [1, 2]] },
            1,
            0
          ]
        }
      },
      "avg_price": { "$avg": "$order_details.items.price" }
    }
  },
  
  // Step 5: Filter categories with > 50 reviews
  {
    "$match": {
      "total_reviews": { "$gt": 50 }
    }
  },
  
  // Step 6: Project and calculate negative review percentage
  {
    "$project": {
      "_id": 0,
      "category_portuguese": "$_id.category_portuguese",
      "category_english": "$_id.category_english",
      "total_reviews": 1,
      "negative_reviews": 1,
      "negative_reviews_percentage": {
        "$round": [
          {
            "$multiply": [
              { "$divide": ["$negative_reviews", "$total_reviews"] },
              100
            ]
          },
          2
        ]
      },
      "avg_price": { "$round": ["$avg_price", 2] }
    }
  },
  
  // Step 7: Sort and limit
  { "$sort": { "negative_reviews_percentage": -1 } },
  { "$limit": 5 }
])
```

---

## Query 3: ROI of Marketing Channels

### Description & Intent
Determine the total revenue generated and the number of recruited sellers for each marketing channel (`origin`), ordered by revenue descending.

### Relational Join Path (SQL)
`marketing_qualified_leads` $\rightarrow$ `closed_deals` $\rightarrow$ `order_items`

### MongoDB Strategy
1. **Source Collection**: `sellers`
2. **Step-by-step**:
   - Filter out sellers that don't have marketing lead `origin` details.
   - `$lookup` the `orders` collection where `orders.items.seller_id` is the current seller's ID.
   - `$unwind` the matching `orders` and `items`.
   - `$match` to ensure we are only accumulating items belonging to this specific seller (since one order could contain products from multiple sellers).
   - Group by marketing `origin` and:
     - Add unique seller IDs to a set using `$addToSet` (to count distinct recruited sellers).
     - Sum item prices.
   - Project: get the size of the seller set and format revenue.
   - Sort by revenue descending.

### MongoDB Aggregation Pipeline
```javascript
db.sellers.aggregate([
  // Step 1: Match sellers recruited via marketing channels
  {
    "$match": {
      "onboarding_details.origin": { "$exists": true, "$ne": null }
    }
  },
  
  // Step 2: Join with orders where the seller sold products
  {
    "$lookup": {
      "from": "orders",
      "localField": "_id",
      "foreignField": "items.seller_id",
      "as": "orders_list"
    }
  },
  { "$unwind": "$orders_list" },
  { "$unwind": "$orders_list.items" },
  
  // Step 3: Match only the specific seller's items
  {
    "$match": {
      "$expr": { "$eq": ["$orders_list.items.seller_id", "$_id"] }
    }
  },
  
  // Step 4: Group by marketing origin channel
  {
    "$group": {
      "_id": "$onboarding_details.origin",
      "sellers_set": { "$addToSet": "$_id" },
      "total_revenue_generated": { "$sum": "$orders_list.items.price" }
    }
  },
  
  // Step 5: Format outputs and calculate size of the sellers set
  {
    "$project": {
      "_id": 0,
      "marketing_origin": "$_id",
      "recruited_sellers": { "$size": "$sellers_set" },
      "total_revenue_generated": { "$round": ["$total_revenue_generated", 2] }
    }
  },
  
  // Step 6: Sort by revenue descending
  { "$sort": { "total_revenue_generated": -1 } }
])
```

---

## Query 4: Impact of Delivery Delays on Satisfaction

### Description & Intent
Correlate delivery delays (actual delivery date vs. estimated delivery date) with average customer review scores. Categorize orders as 'Late Delivery' or 'On Time or Early'.

### Relational Join Path (SQL)
`orders` $\rightarrow$ `reviews`

### MongoDB Strategy
1. **Source Collection**: `orders`
2. **Step-by-step**:
   - Filter out orders where `delivered_customer_date` or `estimated_delivery_date` are empty or null.
   - `$lookup` the `reviews` collection where the order ID matches.
   - `$unwind` the matching `reviews`.
   - Compares date strings as Date objects using `$dateFromString` and `$cond` to group orders into "Late Delivery" or "On Time or Early".
   - Group by the calculated delivery status, summing unique order IDs and averaging the review score.
   - Project clean outputs.

### MongoDB Aggregation Pipeline
```javascript
db.orders.aggregate([
  // Step 1: Filter out orders with missing delivery dates
  {
    "$match": {
      "delivered_customer_date": { "$exists": true, "$ne": null, "$ne": "" },
      "estimated_delivery_date": { "$exists": true, "$ne": null, "$ne": "" }
    }
  },
  
  // Step 2: Join with reviews
  {
    "$lookup": {
      "from": "reviews",
      "localField": "_id",
      "foreignField": "order_id",
      "as": "reviews_details"
    }
  },
  { "$unwind": "$reviews_details" },
  
  // Step 3: Categorize status by parsing date strings
  {
    "$addFields": {
      "delivery_status": {
        "$cond": [
          {
            "$gt": [
              { "$dateFromString": { "dateString": "$delivered_customer_date" } },
              { "$dateFromString": { "dateString": "$estimated_delivery_date" } }
            ]
          },
          "Late Delivery",
          "On Time or Early"
        ]
      }
    }
  },
  
  // Step 4: Group by delivery status
  {
    "$group": {
      "_id": "$delivery_status",
      "orders_set": { "$addToSet": "$_id" },
      "avg_review_score": { "$avg": "$reviews_details.review_score" }
    }
  },
  
  // Step 5: Project outputs
  {
    "$project": {
      "_id": 0,
      "delivery_status": "$_id",
      "total_orders": { "$size": "$orders_set" },
      "avg_review_score": { "$round": ["$avg_review_score", 2] }
    }
  }
])
```

---

## Query 5: Geographical Shipping Bottlenecks

### Description & Intent
Find customer states where the average freight-to-price ratio is above 30%, showing shipping costs relative to purchase price, ordered by the ratio descending.

### Relational Join Path (SQL)
`orders` $\rightarrow$ `customers` $\rightarrow$ `order_items`

### MongoDB Strategy
* **NO LOOKUPS REQUIRED!**
  Because customer details (including state) and order items (including price and freight value) are **pre-embedded** within our `orders` collection schema, this complex SQL query is processed with **zero joins** in MongoDB. This demonstrates the performance efficiency of the document store.
1. **Source Collection**: `orders`
2. **Step-by-step**:
   - `$unwind` the pre-embedded `items` array.
   - Group by customer state (`customer.state`) and calculate the sum of price and freight values. Collect unique order IDs in a set.
   - Project: calculate ratio `(total_freight / total_revenue) * 100` and get order count.
   - Filter (HAVING equivalent) where ratio $> 30\%$.
   - Sort by percentage descending.

### MongoDB Aggregation Pipeline
```javascript
db.orders.aggregate([
  // Step 1: Unwind pre-embedded items
  { "$unwind": "$items" },
  
  // Step 2: Group by customer state (Zero Joins!)
  {
    "$group": {
      "_id": "$customer.state",
      "orders_set": { "$addToSet": "$_id" },
      "total_revenue": { "$sum": "$items.price" },
      "total_freight": { "$sum": "$items.freight_value" }
    }
  },
  
  // Step 3: Project ratios and counts
  {
    "$project": {
      "_id": 0,
      "customer_state": "$_id",
      "total_orders": { "$size": "$orders_set" },
      "total_revenue": { "$round": ["$total_revenue", 2] },
      "freight_to_price_percentage": {
        "$round": [
          {
            "$multiply": [
              {
                "$cond": [
                  { "$eq": ["$total_revenue", 0] },
                  0,
                  { "$divide": ["$total_freight", "$total_revenue"] }
                ]
              },
              100
            ]
          },
          2
        ]
      }
    }
  },
  
  // Step 4: Apply HAVING filter (percentage > 30%)
  {
    "$match": {
      "freight_to_price_percentage": { "$gt": 30.0 }
    }
  },
  
  // Step 5: Sort descending
  { "$sort": { "freight_to_price_percentage": -1 } }
])
```
