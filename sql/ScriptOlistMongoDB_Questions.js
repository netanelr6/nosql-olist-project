/* ==============================================================================
   Olist E-Commerce - HW2 MongoDB Aggregation Queries (Task 4)
   Description: JavaScript queries to be executed in MongoDB Shell or Mongo Express.
                These queries correspond to the 5 relational SQL queries from HW1,
                fully adapted to MongoDB's nested/embedded document model.
   ============================================================================== */

// ------------------------------------------------------------
// Question 1: Sales Agents Rating by Supplier Quality
// Mapped Join Path: reviews -> orders -> sellers (onboarding_details)
// ------------------------------------------------------------
// use olist_db;

db.reviews.aggregate([
  { "$unwind": "$order_id" },
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
  {
    "$lookup": {
      "from": "sellers",
      "localField": "order_details.items.seller_id",
      "foreignField": "_id",
      "as": "seller_details"
    }
  },
  { "$unwind": "$seller_details" },
  {
    "$match": {
      "seller_details.onboarding_details.sr_id": { "$exists": true, "$ne": null }
    }
  },
  {
    "$group": {
      "_id": {
        "sr_id": "$seller_details.onboarding_details.sr_id",
        "review_id": "$_id"
      },
      "review_score": { "$first": "$review_score" }
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
]);

// ------------------------------------------------------------
// Question 2: Product Categories with Negative Reviews
// Mapped Join Path: reviews -> orders -> products (embedded translations)
// ------------------------------------------------------------
db.reviews.aggregate([
  { "$unwind": "$order_id" },
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
  {
    "$lookup": {
      "from": "products",
      "localField": "order_details.items.product_id",
      "foreignField": "_id",
      "as": "product_details"
    }
  },
  { "$unwind": "$product_details" },
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
]);

// ------------------------------------------------------------
// Question 3: ROI of Marketing Channels
// Mapped Join Path: sellers -> orders
// ------------------------------------------------------------
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
]);

// ------------------------------------------------------------
// Question 4: Impact of Delivery Delays on Satisfaction
// Mapped Join Path: orders -> reviews
// ------------------------------------------------------------
db.orders.aggregate([
  {
    "$match": {
      "delivered_customer_date": { "$exists": true, "$ne": null, "$ne": "" },
      "estimated_delivery_date": { "$exists": true, "$ne": null, "$ne": "" }
    }
  },
  {
    "$lookup": {
      "from": "reviews",
      "localField": "_id",
      "foreignField": "order_id",
      "as": "reviews_details"
    }
  },
  { "$unwind": "$reviews_details" },
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
  {
    "$group": {
      "_id": "$delivery_status",
      "orders_set": { "$addToSet": "$_id" },
      "avg_review_score": { "$avg": "$reviews_details.review_score" }
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
]);

// ------------------------------------------------------------
// Question 5: Geographical Shipping Bottlenecks
// Mapped Join Path: orders (Zero Joins!)
// ------------------------------------------------------------
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
]);
