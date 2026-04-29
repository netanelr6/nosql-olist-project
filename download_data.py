import os

# Set Kaggle config dir to current folder so it finds kaggle.json right here
# NOTE: This MUST be done before importing the 'kaggle' module!
os.environ['KAGGLE_CONFIG_DIR'] = os.path.dirname(os.path.abspath(__file__))

import kaggle

def download_olist_data():
    # Define the target path for the downloaded CSVs (a folder named 'data')
    download_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
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