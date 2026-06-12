import os
import pandas as pd
from sqlalchemy import create_engine

def load_csv_to_postgres():
    """
    Ingests raw CSV files from the local 'data' directory into the PostgreSQL database.
    This step recreates the original relational schema before any NoSQL transformations.
    """
    print("Initializing SQL ingestion process...")
    
    # Database connection URI for PostgreSQL running inside the Docker network.
    # Format: postgresql://username:password@container_name:port/database_name
    db_uri = "postgresql://admin:pass@postgres:5432/olist_sql"
    engine = create_engine(db_uri)

    data_dir = "data/"
    
    # Identify all CSV files in the data directory
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    if not csv_files:
        print("Error: No CSV files found in the 'data/' directory.")
        return

    for file in csv_files:
        # The table name will be the filename without the '.csv' extension
        table_name = file.replace('.csv', '')
        file_path = os.path.join(data_dir, file)
        
        print(f"Loading '{file}' into table '{table_name}'...")
        
        # Load data in chunks to optimize memory usage (Best practice for large datasets)
        chunksize = 10000
        for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunksize)):
            # 'replace' creates the table on the first chunk, 'append' adds subsequent chunks
            if_exists = 'replace' if i == 0 else 'append'
            chunk.to_sql(name=table_name, con=engine, if_exists=if_exists, index=False)
            
    print("SQL ingestion completed successfully.")

if __name__ == "__main__":
    load_csv_to_postgres()