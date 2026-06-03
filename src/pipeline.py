import os
import json
import pandas as pd
import logging
from utils import (
    clean_logistics_data, validate_data,
    create_dim_geography, map_geography_to_facts,
    load_to_sqlite
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def load_config(config_path="config/settings.json"):
    with open(config_path, 'r') as f:
        return json.load(f)


def run_pipeline():
    config = load_config()
    raw_dir = config['paths']['raw_dir']

    files = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
    if not files:
        logging.info("No new files to process.")
        return

    for file_name in files:
        logging.info(f"Processing: {file_name}")

        # ── 1. EXTRACT ────────────────────────────────────────────────────────
        df = pd.read_csv(
            os.path.join(raw_dir, file_name),
            encoding='latin-1'
        )
        logging.info(f"Loaded {len(df):,} rows × {df.shape[1]} columns")

        # ── 2. TRANSFORM ──────────────────────────────────────────────────────
        df = clean_logistics_data(df, config)

        # Build Dim_Geography BEFORE dropping geo columns from the fact table
        dim_geo = create_dim_geography(df, config)
        df = map_geography_to_facts(df, dim_geo, config)

        clean_df, quarantine_df = validate_data(df)

        # Dimension tables
        dim_customer = (
            clean_df[config['customer_cols']]
            .drop_duplicates(subset=['Customer Id'])
        )
        dim_product = (
            clean_df[config['product_cols']]
            .drop_duplicates(subset=['Product Card Id'])
        )
        dim_product_category = (
            clean_df[config['product_category_cols']]
            .drop_duplicates(subset=['Category Id'])
        )
        dim_product_department = (
            clean_df[config['product_department_cols']]
            .drop_duplicates(subset=['Department Id'])
        )

        # Fact tables
        fact_header = (
            clean_df[config['order_header_cols']]
            .drop_duplicates(subset=['Order Id'])
        )
        fact_lineitem = clean_df[config['order_lineitem_cols']]

        schema_tables = {
            "Dim_Product_Category":   dim_product_category,
            "Dim_Product_Department": dim_product_department,
            "Dim_Geography":          dim_geo,
            "Dim_Customer":           dim_customer,
            "Dim_Product":            dim_product,
            "Fact_Order_Header":      fact_header,
            "Fact_Order_LineItem":    fact_lineitem,
        }

        # ── 3. LOAD ───────────────────────────────────────────────────────────
        load_to_sqlite(schema_tables, db_name=config['paths']['db_path'])

        # ── 4. QUARANTINE ─────────────────────────────────────────────────────
        if not quarantine_df.empty:
            quarantine_path = os.path.join(
                config['paths']['quarantine_dir'],
                f"quarantine_{file_name}"
            )
            quarantine_df.to_csv(quarantine_path, index=False)
            logging.warning(
                f"Quarantined {len(quarantine_df):,} rows → {quarantine_path}"
            )

        # ── 5. ARCHIVE ────────────────────────────────────────────────────────
        os.rename(
            os.path.join(raw_dir, file_name),
            os.path.join(config['paths']['archive_dir'], file_name)
        )
        logging.info(f"Archived: {file_name}")


if __name__ == "__main__":
    run_pipeline()