import os
import sys
import logging
from sqlalchemy import create_engine, inspect, text
from pymongo import MongoClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def verify_sql():
    logging.info("--- VERIFYING POSTGRESQL (SQL) ---")
    postgres_uri = os.environ.get("POSTGRES_URI", "postgresql://admin:pass@localhost:5432/olist_sql")
    try:
        engine = create_engine(postgres_uri)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            logging.warning("No tables found in PostgreSQL database.")
            return False
            
        logging.info(f"Found {len(tables)} tables in SQL database:")
        for table in sorted(tables):
            with engine.connect() as conn:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = res.scalar()
                logging.info(f" - Table '{table}': {count} rows")
        return True

    except Exception as e:
        logging.error(f"Error connecting or querying PostgreSQL: {e}")
        return False

def verify_mongo():
    logging.info("--- VERIFYING MONGODB (NOSQL) ---")
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    try:
        client = MongoClient(mongo_uri)
        db = client["olist_db"]
        collections = db.list_collection_names()
        
        if not collections:
            logging.warning("No collections found in MongoDB database.")
            return False
            
        logging.info(f"Found {len(collections)} collections in MongoDB:")
        for coll in sorted(collections):
            count = db[coll].count_documents({})
            logging.info(f" - Collection '{coll}': {count} documents")
        return True
    except Exception as e:
        logging.error(f"Error connecting or querying MongoDB: {e}")
        return False

def main():
    logging.info("=== Starting Data Ingestion Verification ===")
    sql_ok = verify_sql()
    mongo_ok = verify_mongo()
    
    if sql_ok and mongo_ok:
        logging.info("=== Verification Complete: All systems operational ===")
        sys.exit(0)
    else:
        logging.error("=== Verification Failed: One or both databases are empty or unreachable ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
