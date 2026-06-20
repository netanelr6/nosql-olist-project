import os
import time
import json
from flask import Flask, render_template, jsonify, request
from sqlalchemy import create_engine, text
from pymongo import MongoClient


app = Flask(__name__)

# Resolve database URIs (fallback to localhost for host execution)
postgres_uri = os.getenv("POSTGRES_URI", "postgresql://admin:pass@localhost:5432/olist_sql")
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# Initialize Database Clients
try:
    sql_engine = create_engine(postgres_uri)
except Exception as e:
    sql_engine = None
    print(f"PostgreSQL connection error: {e}")

try:
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client["olist_db"]
except Exception as e:
    mongo_db = None
    print(f"MongoDB connection error: {e}")

# Predefined Queries Dictionary
queries = {
    "1": {
        "title": "שאילתה 1: דירוג אנשי מכירות לפי איכות ספקים (HR)",
        "sql": """SELECT 
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
LIMIT 5;""",
        "mongo_collection": "sellers",
        "mongo_pipeline": [
            {
                "$match": {
                    "onboarding_details.sr_id": { "$exists": True, "$ne": None }
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
        ]
    },
    "2": {
        "title": "שאילתה 2: קטגוריות מוצרים עם אחוז ביקורות שליליות גבוה",
        "sql": """SELECT 
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
LIMIT 5;""",
        "mongo_collection": "orders",
        "mongo_pipeline": [
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
        ]
    },
    "3": {
        "title": "שאילתה 3: החזר השקעה (ROI) של ערוצי שיווק שונים",
        "sql": """SELECT 
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
    total_revenue_generated DESC;""",
        "mongo_collection": "sellers",
        "mongo_pipeline": [
            {
                "$match": {
                    "onboarding_details.origin": { "$exists": True, "$ne": None }
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
        ]
    },
    "4": {
        "title": "שאילתה 4: השפעת איחור במסירת המשלוח על שביעות רצון הלקוח",
        "sql": """SELECT 
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
    END;""",
        "mongo_collection": "orders",
        "mongo_pipeline": [
            {
                "$match": {
                    "delivered_customer_date": { "$exists": True, "$ne": None },
                    "estimated_delivery_date": { "$exists": True, "$ne": None }
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
        ]
    },
    "5": {
        "title": "שאילתה 5: חסמי שילוח גיאוגרפיים (משלוח מעל 30%)",
        "sql": """SELECT 
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
    freight_to_price_percentage DESC;""",
        "mongo_collection": "orders",
        "mongo_pipeline": [
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
        ]
    }
}

@app.route("/")
def index():
    return render_template("index.html", queries=queries)

@app.route("/api/queries")
def get_queries():
    return jsonify(queries)

@app.route("/api/run", methods=["POST"])
def run_query():
    data = request.get_json()
    query_id = data.get("query_id")
    db_type = data.get("db_type") # "sql" or "mongodb"
    custom_code = data.get("custom_code")
    
    if not query_id or query_id not in queries:
        return jsonify({"error": "Invalid Query ID"}), 400
        
    query_info = queries[query_id]
    
    if db_type == "sql":
        if not sql_engine:
            return jsonify({"error": "PostgreSQL is not connected."}), 500
        
        sql_to_run = custom_code if custom_code else query_info["sql"]
        
        start_time = time.perf_counter()
        try:
            with sql_engine.connect() as conn:
                # 1. Run actual query
                result = conn.execute(text(sql_to_run))
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()[:100]] # Limit to 100 rows for UI speed
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000
                
                # 2. Get explain stats (for query load details)
                explain_plan = ""
                try:
                    explain_res = conn.execute(text(f"EXPLAIN ANALYZE {sql_to_run}"))
                    explain_plan = "\n".join([r[0] for r in explain_res.fetchall()])
                except Exception as e_ex:
                    explain_plan = f"Explain failed: {e_ex}"
                
                return jsonify({
                    "success": True,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "rows_returned": len(rows),
                    "output": rows,
                    "columns": columns,
                    "explain_plan": explain_plan
                })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    elif db_type == "mongodb":
        if mongo_db is None:
            return jsonify({"error": "MongoDB is not connected."}), 500
        
        collection_name = query_info["mongo_collection"]
        
        try:
            pipeline = json.loads(custom_code) if custom_code else query_info["mongo_pipeline"]
        except Exception as pe:
            return jsonify({"success": False, "error": f"JSON parsing error: {pe}"}), 400
            
        start_time = time.perf_counter()
        try:
            coll = mongo_db[collection_name]
            cursor = coll.aggregate(pipeline)
            docs = list(cursor)[:100] # Limit to 100 docs
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000
            
            # Get explain metrics
            explain_stats = {}
            try:
                explain_res = mongo_db.command(
                    'explain', 
                    {'aggregate': collection_name, 'pipeline': pipeline, 'cursor': {}}, 
                    verbosity='executionStats'
                )
                
                # Extract key stats
                stages = explain_res.get("stages", [])
                stats = {}
                if stages and isinstance(stages, list) and "$cursor" in stages[0]:
                    cursor_data = stages[0]["$cursor"]
                    stats = cursor_data.get("executionStats", {})
                else:
                    stats = explain_res.get("executionStats", {})
                
                # Traverse nested explain outputs if needed, or return simplified values
                explain_stats = {
                    "totalDocsExamined": stats.get("totalDocsExamined", 0),
                    "totalKeysExamined": stats.get("totalKeysExamined", 0),
                    "executionTimeMillis": stats.get("executionTimeMillis", 0),
                    "nReturned": stats.get("nReturned", 0),
                    "raw": json.dumps(explain_res, indent=2, default=str)
                }
            except Exception as e_ex:
                explain_stats = {"error": f"Explain command failed: {e_ex}"}

            return jsonify({
                "success": True,
                "execution_time_ms": round(execution_time_ms, 2),
                "rows_returned": len(docs),
                "output": docs,
                "explain_plan": explain_stats
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    else:
        return jsonify({"error": "Invalid database type"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8083, debug=True)
