import pandas as pd
from pymongo import MongoClient
import json
import os

def load_data():
    print("Connecting to MongoDB...")
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(mongo_uri)
    
    # Drop and recreate database
    client.drop_database('olist_db')
    db = client["olist_db"]
    
    # Resolve data directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")

    def df_to_docs(df):
        return json.loads(df.to_json(orient='records'))

    # 1. Load Products Collection (with English translations)
    print("Loading Products Collection...")
    products = pd.read_csv(os.path.join(data_dir, "olist_products_dataset.csv"))
    translations = pd.read_csv(os.path.join(data_dir, "product_category_name_translation.csv"))
    products_merged = pd.merge(products, translations, on="product_category_name", how="left")
    products_merged['_id'] = products_merged['product_id']
    products_merged.drop('product_id', axis=1, inplace=True)
    db.products.insert_many(df_to_docs(products_merged))

    # 2. Load Sellers Collection (with marketing funnel details)
    print("Loading Sellers Collection (with Onboarding Details)...")
    sellers = pd.read_csv(os.path.join(data_dir, "olist_sellers_dataset.csv"))
    closed_deals = pd.read_csv(os.path.join(data_dir, "olist_closed_deals_dataset.csv"))
    mql = pd.read_csv(os.path.join(data_dir, "olist_marketing_qualified_leads_dataset.csv"))
    funnel = pd.merge(closed_deals, mql, on="mql_id", how="left")
    sellers_merged = pd.merge(sellers, funnel, on="seller_id", how="left")
    
    sellers_docs = []
    for doc in df_to_docs(sellers_merged):
        seller_doc = {
            "_id": doc["seller_id"],
            "city": doc["seller_city"],
            "state": doc["seller_state"],
            "zip_code_prefix": doc["seller_zip_code_prefix"]
        }
        if doc.get("mql_id"):
            seller_doc["onboarding_details"] = {
                "mql_id": doc["mql_id"],
                "first_contact_date": doc["first_contact_date"],
                "origin": doc["origin"],
                "sr_id": doc["sr_id"],
                "business_segment": doc["business_segment"]
            }
        sellers_docs.append(seller_doc)
    db.sellers.insert_many(sellers_docs)

    # 3. Load Reviews Collection mapped by order_id (and main collection for backwards compatibility)
    print("Loading Reviews Collection...")
    reviews = pd.read_csv(os.path.join(data_dir, "olist_order_reviews_dataset.csv"))
    
    # Map order_id to list of review summaries to embed in orders
    order_reviews_map = {}
    for idx, row in reviews.iterrows():
        oid = row["order_id"]
        review_detail = {
            "review_id": row["review_id"],
            "review_score": int(row["review_score"]) if not pd.isna(row["review_score"]) else 5,
            "review_comment_title": row["review_comment_title"] if not pd.isna(row["review_comment_title"]) else "",
            "review_comment_message": row["review_comment_message"] if not pd.isna(row["review_comment_message"]) else "",
            "review_creation_date": row["review_creation_date"] if not pd.isna(row["review_creation_date"]) else ""
        }
        if oid not in order_reviews_map:
            order_reviews_map[oid] = []
        order_reviews_map[oid].append(review_detail)

    # Group identical reviews for independent reviews collection
    reviews_grouped = reviews.groupby("review_id").agg({
        "order_id": lambda x: list(x),
        "review_score": "first",
        "review_comment_title": "first",
        "review_comment_message": "first",
        "review_creation_date": "first"
    }).reset_index()
    reviews_grouped['_id'] = reviews_grouped['review_id']
    reviews_grouped.drop('review_id', axis=1, inplace=True)
    db.reviews.insert_many(df_to_docs(reviews_grouped))

    # 4. Load Orders Collection (combining customers, denormalized items and embedded reviews)
    print("Loading Orders Collection (with Denormalization)...")
    orders = pd.read_csv(os.path.join(data_dir, "olist_orders_dataset.csv"))
    customers = pd.read_csv(os.path.join(data_dir, "olist_customers_dataset.csv"))
    items = pd.read_csv(os.path.join(data_dir, "olist_order_items_dataset.csv"))
    payments = pd.read_csv(os.path.join(data_dir, "olist_order_payments_dataset.csv"))

    # Convert date columns to datetime
    for col in ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        orders[col] = pd.to_datetime(orders[col], errors='coerce')

    # Merge items with products to embed product category details inside the items array
    items_with_products = pd.merge(items, products_merged, left_on="product_id", right_on="_id", how="left")
    items_with_products.drop(["_id"], axis=1, inplace=True, errors="ignore")

    orders_merged = pd.merge(orders, customers, on="customer_id", how="left")
    
    items_records = df_to_docs(items_with_products)
    items_df = pd.DataFrame(items_records)
    items_dict = items_df.groupby("order_id").apply(lambda x: json.loads(x.drop("order_id", axis=1).to_json(orient='records'))).to_dict()
    payments_dict = payments.groupby("order_id").apply(lambda x: df_to_docs(x.drop("order_id", axis=1))).to_dict()

    orders_docs = []
    for idx, row in orders_merged.iterrows():
        order_id = row["order_id"]
        
        # Helper to convert pandas Timestamps to python datetimes
        def get_dt(val):
            if pd.isna(val):
                return None
            return val.to_pydatetime()

        order_doc = {
            "_id": order_id,
            "order_status": row["order_status"],
            "purchase_timestamp": get_dt(row["order_purchase_timestamp"]),
            "delivered_customer_date": get_dt(row["order_delivered_customer_date"]),
            "estimated_delivery_date": get_dt(row["order_estimated_delivery_date"]),
            "customer": {
                "customer_id": row["customer_id"],
                "unique_id": row["customer_unique_id"],
                "zip_code_prefix": int(row["customer_zip_code_prefix"]),
                "city": row["customer_city"],
                "state": row["customer_state"]
            },
            "items": items_dict.get(order_id, []),
            "payments": payments_dict.get(order_id, []),
            "reviews": order_reviews_map.get(order_id, [])
        }
        orders_docs.append(order_doc)
        
    db.orders.insert_many(orders_docs)

    print("Creating optimized indexes in MongoDB...")
    db.orders.create_index("items.seller_id")
    db.orders.create_index("items.product_id")
    db.orders.create_index("customer.state")
    db.reviews.create_index("order_id")

    print("Data loaded to MongoDB successfully! Olist NoSQL Project is ready.")

if __name__ == "__main__":
    load_data()