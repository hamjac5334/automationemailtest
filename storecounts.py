import os
import pandas as pd

DOWNLOAD_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")

def add_store_value_counts(csv_path, distributor_col='Distributor Location', product_col='Product Name', store_col='Retailer'):
    df = pd.read_csv(csv_path)
    value_counts = df.groupby([distributor_col, product_col])[store_col].nunique().reset_index()
    value_counts.rename(columns={store_col: 'StoreCount'}, inplace=True)
    df = pd.merge(df, value_counts, on=[distributor_col, product_col], how='left')
    return df

def load_last_report():
    """Assumes last report is newest file in DOWNLOAD_DIR."""
    files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.csv')]
    full_paths = [os.path.join(DOWNLOAD_DIR, f) for f in files]
    last_file = max(full_paths, key=os.path.getmtime)
    return last_file

def load_specific_report(filename_contains):
    files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.csv') and filename_contains in f]
    full_paths = [os.path.join(DOWNLOAD_DIR, f) for f in files]
    if not full_paths:
        raise FileNotFoundError(f"No CSV file containing '{filename_contains}' found")
    return full_paths[0]

def merge_three_storecounts_reports():
    # Load and process each storecount CSV
    csv_30 = load_specific_report("_5.csv")   # original 30 days
    csv_60 = load_specific_report("_6.csv")   # 60 days
    csv_90 = load_specific_report("_7.csv")   # 90 days

    df_30 = add_store_value_counts(csv_30)
    df_60 = add_store_value_counts(csv_60)
    df_90 = add_store_value_counts(csv_90)

    # Possibly rename StoreCount columns for clarity
    df_30 = df_30.rename(columns={'StoreCount': 'StoreCount_30days'})
    df_60 = df_60.rename(columns={'StoreCount': 'StoreCount_60days'})
    df_90 = df_90.rename(columns={'StoreCount': 'StoreCount_90days'})

    merge_cols = ['Distributor Location', 'Product Name']
    # Merge 30 and 60 days
    merged = pd.merge(df_30[merge_cols + ['StoreCount_30days']],
                      df_60[merge_cols + ['StoreCount_60days']],
                      how='outer',
                      on=merge_cols)
    # Merge result with 90 days
    merged = pd.merge(merged,
                      df_90[merge_cols + ['StoreCount_90days']],
                      how='outer',
                      on=merge_cols)
    return merged


