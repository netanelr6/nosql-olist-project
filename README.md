# Olist E-Commerce NoSQL Project

## Overview
This project is part of the Advanced Database Technologies (NoSQL) course at Ben-Gurion University. 
The goal of this project is to model and analyze the Brazilian E-Commerce Public Dataset by Olist, along with its Marketing Funnel extension.

## Phase 1: Relational Modeling (PostgreSQL)
In the first phase, we established a solid relational foundation:
- Downloaded the raw datasets using the Kaggle API.
- Designed an Entity-Relationship Diagram (ERD) encompassing 10 tables.
- Implemented the schema in PostgreSQL, connecting the E-commerce operational data with the Marketing Funnel data (linking `closed_deals` to `sellers`).

## Setup
To download the data locally:
1. Ensure your `kaggle.json` is in the root directory.
2. Run the download script:
   `python download_data.py`