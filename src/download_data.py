import os

# Set Kaggle config dir to parent folder (root) so it finds kaggle.json right there
# NOTE: This MUST be done before importing the 'kaggle' module!
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ['KAGGLE_CONFIG_DIR'] = parent_dir

import kaggle

def download_olist_data():
    # Define the target path for the downloaded CSVs (a folder named 'data' in the root)
    download_path = os.path.join(parent_dir, 'data')
    
    # Create the 'data' directory if it does not exist
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    print("Starting download for Brazilian E-Commerce dataset...")
    # Download and extract the main e-commerce dataset
    kaggle.api.dataset_download_cli('olistbr/brazilian-ecommerce', unzip=True, path=download_path)
    
    print("Starting download for Marketing Funnel dataset...")
    # Download and extract the marketing funnel extension dataset
    kaggle.api.dataset_download_cli('olistbr/marketing-funnel-olist', unzip=True, path=download_path)
    
    print("Download and extraction complete! All CSV files are ready in the 'data' folder.")

if __name__ == "__main__":
    download_olist_data()