import subprocess
import sys
import logging

# Configure professional logging formatting to track pipeline execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def run_script(script_name):
    """
    Executes a Python script as a subprocess and monitors its execution.
    Raises an exception and halts the pipeline if a script fails.
    
    Args:
        script_name (str): The filename of the Python script to execute.
    """
    logging.info(f"Triggering execution of: {script_name}")
    try:
        # Run the script. 'check=True' ensures an exception is raised on failure.
        result = subprocess.run(
            [sys.executable, script_name], 
            check=True, 
            text=True, 
            capture_output=True
        )
        logging.info(f"Successfully completed: {script_name}\nOutput Summary:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"FATAL ERROR executing {script_name}.\nError Output:\n{e.stderr}")
        sys.exit(1) # Halt the entire pipeline

def main():
    """
    Main orchestrator for the End-to-End ETL Pipeline.
    Coordinates data extraction, relational loading (SQL), and NoSQL transformation.
    """
    logging.info("=== Initializing Olist E-Commerce ETL Pipeline ===")

    # Step 1: Extract (Download datasets from Kaggle)
    # Note: Requires Kaggle API credentials (kaggle.json) inside the container environment.
    logging.info("--- STEP 1: Data Extraction (Kaggle) ---")
    run_script('download_data.py')

    # Step 2: Load to Relational Database (PostgreSQL)
    logging.info("--- STEP 2: Relational Ingestion (PostgreSQL) ---")
    run_script('load_to_sql.py')

    # Step 3: Transform and Load to Document Database (MongoDB)
    logging.info("--- STEP 3: NoSQL Transformation & Ingestion (MongoDB) ---")
    run_script('load_to_mongo.py')

    logging.info("=== ETL Pipeline Execution Completed Successfully ===")

if __name__ == "__main__":
    main()