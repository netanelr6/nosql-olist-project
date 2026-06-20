# Olist Project - MongoDB (NoSQL) Aggregation Queries

This document contains the complete set of optimized MongoDB aggregation queries used in the project, designed to run against the denormalized database schema.

---

## 📂 Query 1: Sales Representative (SR) Performance (HR Analysis)
Find the top 5 sales representatives (SDR/SR) who onboarded sellers with the highest average review scores (for reps with more than 10 reviews).

```json
db.sellers.aggregate([
  {
    "$match": {
      "onboarding_details.sr_id": { "$exists": true, "$ne": null }
    }
  },
  {
    "$lookup": {
      "from": "orders",
      "localField": "_id",
      "foreignField": "items.seller_id",
      "as": "orders_list"
    }
  },
  { "$unwind": "$orders_list" },
  { "$unwind": "$orders_list.reviews" },
  { "$unwind": "$orders_list.items" },
  {
    "$match": {
      "$expr": { "$eq": ["$orders_list.items.seller_id", "$_id"] }
    }
  },
  {
    "$group": {
      "_id": {
        "sr_id": "$onboarding_details.sr_id",
        "review_id": "$orders_list.reviews.review_id"
      },
      "review_score": { "$first": "$orders_list.reviews.review_score" }
    }
  },
  {
    "$group": {
      "_id": "$_id.sr_id",
      "total_reviews": { "$sum": 1 },
      "avg_review_score": { "$avg": "$review_score" }
    }
  },
  {
    "$match": {
      "total_reviews": { "$gt": 10 }
    }
  },
  { "$sort": { "avg_review_score": -1 } },
  { "$limit": 5 },
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

## 📂 Query 2: Product Categories with High Negative Reviews
Identify the top 5 product categories with the highest percentage of negative reviews (scores of 1 or 2), alongside the average price of products in those categories (for categories with over 50 reviews).

```json
db.orders.aggregate([
  { "$unwind": "$reviews" },
  { "$unwind": "$items" },
  {
    "$group": {
      "_id": {
        "category_portuguese": "$items.product_category_name",
        "category_english": "$items.product_category_name_english"
      },
      "total_reviews": { "$sum": 1 },
      "negative_reviews": {
        "$sum": {
          "$cond": [
            { "$in": ["$reviews.review_score", [1, 2]] },
            1,
            0
          ]
        }
      },
      "avg_price": { "$avg": "$items.price" }
    }
  },
  {
    "$match": {
      "total_reviews": { "$gt": 50 }
    }
  },
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
  { "$sort": { "negative_reviews_percentage": -1 } },
  { "$limit": 5 }
])
```

---

## 📂 Query 3: ROI of Marketing Funnel Channels
Find the total revenue generated and the count of unique recruited sellers for each marketing channel lead origin.

```json
db.sellers.aggregate([
  {
    "$match": {
      "onboarding_details.origin": { "$exists": true, "$ne": null }
    }
  },
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
  {
    "$match": {
      "$expr": { "$eq": ["$orders_list.items.seller_id", "$_id"] }
    }
  },
  {
    "$group": {
      "_id": "$onboarding_details.origin",
      "sellers_set": { "$addToSet": "$_id" },
      "total_revenue_generated": { "$sum": "$orders_list.items.price" }
    }
  },
  {
    "$project": {
      "_id": 0,
      "marketing_origin": "$_id",
      "recruited_sellers": { "$size": "$sellers_set" },
      "total_revenue_generated": { "$round": ["$total_revenue_generated", 2] }
    }
  },
  { "$sort": { "total_revenue_generated": -1 } }
])
```

---

## 📂 Query 4: Impact of Shipping Delays on Review Scores
Compare average review scores for orders that were delivered on-time or early vs. orders delivered late.

```json
db.orders.aggregate([
  {
    "$match": {
      "delivered_customer_date": { "$exists": true, "$ne": null },
      "estimated_delivery_date": { "$exists": true, "$ne": null }
    }
  },
  { "$unwind": "$reviews" },
  {
    "$addFields": {
      "delivery_status": {
        "$cond": [
          {
            "$gt": [
              "$delivered_customer_date",
              "$estimated_delivery_date"
            ]
          },
          "Late Delivery",
          "On Time or Early"
        ]
      }
    }
  },
  {
    "$group": {
      "_id": "$delivery_status",
      "orders_set": { "$addToSet": "$_id" },
      "avg_review_score": { "$avg": "$reviews.review_score" }
    }
  },
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

## 📂 Query 5: Geographical Shipping Cost Analysis
Identify states in Brazil where the total shipping freight cost exceeds 30% of the total product value.

```json
db.orders.aggregate([
  { "$unwind": "$items" },
  {
    "$group": {
      "_id": "$customer.state",
      "orders_set": { "$addToSet": "$_id" },
      "total_revenue": { "$sum": "$items.price" },
      "total_freight": { "$sum": "$items.freight_value" }
    }
  },
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
  {
    "$match": {
      "freight_to_price_percentage": { "$gt": 30.0 }
    }
  },
  { "$sort": { "freight_to_price_percentage": -1 } }
])
```
