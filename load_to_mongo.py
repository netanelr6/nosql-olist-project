import pandas as pd
from pymongo import MongoClient
import json
import os

def load_data():
    print("Connecting to MongoDB...")
    # התחברות למונגו (שרץ בדוקר)
    client = MongoClient("mongodb://localhost:27017/")
    
    # יצירת בסיס הנתונים (או דריסה אם קיים כדי לא לשכפל)
    client.drop_database('olist_db')
    db = client["olist_db"]
    data_dir = "data/"

    # פונקציית עזר להמרת DataFrame לפורמט שמונגו אוהב (מעלים NaN ל-null)
    def df_to_docs(df):
        return json.loads(df.to_json(orient='records'))

    # ---------------------------------------------------------
    # 1. טעינת אוסף המוצרים (Products) + התרגום לאנגלית
    # ---------------------------------------------------------
    print("Loading Products Collection...")
    products = pd.read_csv(os.path.join(data_dir, "olist_products_dataset.csv"))
    translations = pd.read_csv(os.path.join(data_dir, "product_category_name_translation.csv"))
    
    products_merged = pd.merge(products, translations, on="product_category_name", how="left")
    products_merged['_id'] = products_merged['product_id'] # הגדרת מזהה ראשי
    products_merged.drop('product_id', axis=1, inplace=True)
    
    db.products.insert_many(df_to_docs(products_merged))

    # ---------------------------------------------------------
    # 2. טעינת אוסף המוכרים (Sellers) + נתוני גיוס ושיווק
    # ---------------------------------------------------------
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
        # אם יש נתוני משפך (הוטמע מטבלאות השיווק)
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

    # ---------------------------------------------------------
    # 3. טעינת אוסף הביקורות (Reviews)
    # ---------------------------------------------------------
    print("Loading Reviews Collection...")
    reviews = pd.read_csv(os.path.join(data_dir, "olist_order_reviews_dataset.csv"))
    
    # קיבוץ ביקורות זהות שקשורות למספר הזמנות שונות
    reviews_grouped = reviews.groupby("review_id").agg({
        "order_id": lambda x: list(x), # מערך של references
        "review_score": "first",
        "review_comment_title": "first",
        "review_comment_message": "first",
        "review_creation_date": "first"
    }).reset_index()
    
    reviews_grouped['_id'] = reviews_grouped['review_id']
    reviews_grouped.drop('review_id', axis=1, inplace=True)
    
    db.reviews.insert_many(df_to_docs(reviews_grouped))

    # ---------------------------------------------------------
    # 4. טעינת אוסף ההזמנות (Orders) + לקוחות, פריטים ותשלומים
    # ---------------------------------------------------------
    print("Loading Orders Collection (Combining Customers, Items, and Payments)...")
    orders = pd.read_csv(os.path.join(data_dir, "olist_orders_dataset.csv"))
    customers = pd.read_csv(os.path.join(data_dir, "olist_customers_dataset.csv"))
    items = pd.read_csv(os.path.join(data_dir, "olist_order_items_dataset.csv"))
    payments = pd.read_csv(os.path.join(data_dir, "olist_order_payments_dataset.csv"))

    # חיבור פרטי לקוח להזמנה
    orders_merged = pd.merge(orders, customers, on="customer_id", how="left")
    
    # הכנת הפריטים והתשלומים כמילונים (לשליפה מהירה)
    items_dict = items.groupby("order_id").apply(lambda x: df_to_docs(x.drop("order_id", axis=1))).to_dict()
    payments_dict = payments.groupby("order_id").apply(lambda x: df_to_docs(x.drop("order_id", axis=1))).to_dict()

    orders_docs = []
    for doc in df_to_docs(orders_merged):
        order_id = doc["order_id"]
        order_doc = {
            "_id": order_id,
            "order_status": doc["order_status"],
            "purchase_timestamp": doc["order_purchase_timestamp"],
            "delivered_customer_date": doc["order_delivered_customer_date"],
            "estimated_delivery_date": doc["order_estimated_delivery_date"],
            "customer": {
                "customer_id": doc["customer_id"],
                "unique_id": doc["customer_unique_id"],
                "zip_code_prefix": doc["customer_zip_code_prefix"],
                "city": doc["customer_city"],
                "state": doc["customer_state"]
            },
            "items": items_dict.get(order_id, []),
            "payments": payments_dict.get(order_id, [])
        }
        orders_docs.append(order_doc)
        
    db.orders.insert_many(orders_docs)

    print("Data loaded to MongoDB successfully! Olist NoSQL Project is ready.")

if __name__ == "__main__":
    load_data()