import os
import pandas as pd

DOWNLOAD_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")

def add_store_value_counts(csv_path, distributor_col='Distributor', product_col='Product Name', store_col='Location'):
    """
    Reads the CSV at csv_path, calculates the number of unique stores per product per distributor,
    and returns the augmented DataFrame with a new 'StoreCount' column.
    
    Adjust column names as necessary to match your report's column headers.
    """
    df = pd.read_csv(csv_path)
    
    # Calculate number of unique stores per distributor and product
    value_counts = df.groupby([distributor_col, product_col])[store_col].nunique().reset_index()
    value_counts.rename(columns={store_col: 'StoreCount'}, inplace=True)
    
    # Merge the counts back into the original dataframe
    df = pd.merge(df, value_counts, on=[distributor_col, product_col], how='left')
    
    return df

def load_last_report():
    """
    Finds the most recent CSV report file in the download directory based on modification time
    and returns its path.
    """
    files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.csv')]
    if not files:
        raise FileNotFoundError("No CSV files found in the downloads directory.")
    
    # Full file paths
    full_paths = [os.path.join(DOWNLOAD_DIR, f) for f in files]
    # Most recently modified file
    last_file = max(full_paths, key=os.path.getmtime)
    return last_file

if __name__ == "__main__":
    last_csv = load_last_report()
    print(f"Processing last downloaded CSV report: {last_csv}")
    
    # Compute store counts and add column
    result_df = add_store_value_counts(last_csv)
    
    # Optionally save the updated dataframe as a new CSV for further use or inspection
    output_path = last_csv.replace(".csv", "_with_storecounts.csv")
    result_df.to_csv(output_path, index=False)
    print(f"Augmented report saved to: {output_path}")

