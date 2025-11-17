import os
import pandas as pd

DOWNLOAD_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")

def add_store_value_counts(csv_path, distributor_col='Distributor Location', product_col='Product Name', store_col='Retailer'):
    df = pd.read_csv(csv_path)
    # Calculate value counts per distributor per product
    value_counts = df.groupby([distributor_col, product_col])[store_col].nunique().reset_index()
    return value_counts


def merge_three_storecounts_reports():
    # Assuming downloaded filenames as ..._5.csv, ..._6.csv, ..._7.csv for the 3 time periods
    csv_30 = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('_5.csv')][0]
    csv_60 = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('_6.csv')][0]
    csv_90 = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('_7.csv')][0]

    df_30 = add_store_value_counts(os.path.join(DOWNLOAD_DIR, csv_30))
    df_60 = add_store_value_counts(os.path.join(DOWNLOAD_DIR, csv_60))
    df_90 = add_store_value_counts(os.path.join(DOWNLOAD_DIR, csv_90))

    df_30 = df_30.rename(columns={'Retailer': 'StoreCount_30days'})
    df_60 = df_60.rename(columns={'Retailer': 'StoreCount_60days'})
    df_90 = df_90.rename(columns={'Retailer': 'StoreCount_90days'})

    merge_cols = ['Distributor Location', 'Product Name']
    # Outer merge to keep all entries
    merged = pd.merge(df_30, df_60, how='outer', on=merge_cols)
    merged = pd.merge(merged, df_90, how='outer', on=merge_cols)
    return merged


