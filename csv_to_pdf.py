import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

STORECOUNTS_PATH = None
DOWNLOAD_DIR = None
DASHBOARD_URL = None
_storecounts_df = None
_eda_run_for_first_report = False

def set_storecounts_path(storecounts_path):
    global STORECOUNTS_PATH, _storecounts_df
    STORECOUNTS_PATH = storecounts_path
    if os.path.exists(storecounts_path):
        df = pd.read_csv(storecounts_path)
        df = df.drop_duplicates(subset=['Distributor Location', 'Product Name'])
        _storecounts_df = df
    else:
        _storecounts_df = pd.DataFrame(columns=['Distributor Location', 'Product Name', 'StoreCount'])

def set_eda_config(download_dir, dashboard_url):
    global DOWNLOAD_DIR, DASHBOARD_URL
    DOWNLOAD_DIR = download_dir
    DASHBOARD_URL = dashboard_url

def sort_by_product_order(df):
    PREFIX_ORDER = [
        "Island Coastal Lager",
        "Island Active",
        "Island Chill",
        "Rusty Bull Dance Naked",
        "Rusty Bull Juice Juice",
        "Southern Barrel Damn Yankee",
        "Southern Barrel Helles",
    ]

    SUFFIX_ORDER = [
        "1/6",
        "1/2",
        "2/12",
        "4/6",
        "6/4",
    ]

    def get_prefix_key(product_name):
        name = str(product_name)
        for i, prefix in enumerate(PREFIX_ORDER):
            if name.startswith(prefix):
                return i
        return len(PREFIX_ORDER)

    def get_suffix_key(product_name):
        name = str(product_name)
        for i, suffix in enumerate(SUFFIX_ORDER):
            if suffix in name:
                return i
        return len(SUFFIX_ORDER)

    df = df.copy()

    # Pin these rows to the top regardless of position
    pinned_mask = df["Product Name"].isin(["Total", "<i>*Products Not mapped</i>"])
    pinned_rows = df[pinned_mask]
    rest = df[~pinned_mask].copy()

    rest["_prefix_key"] = rest["Product Name"].apply(get_prefix_key)
    rest["_suffix_key"] = rest["Product Name"].apply(get_suffix_key)
    rest = rest.sort_values(["_prefix_key", "_suffix_key"]).drop(columns=["_prefix_key", "_suffix_key"])

    df = pd.concat([pinned_rows, rest]).reset_index(drop=True)
    return df

def csv_to_pdf(csv_path, run_eda_on_first=False, skip_location_total=False):
    global _storecounts_df, _eda_run_for_first_report

    df = pd.read_csv(csv_path)

    if _storecounts_df is not None and not _storecounts_df.empty:
        if 'Location' in df.columns and 'Product Name' in df.columns and \
                'Distributor Location' in _storecounts_df.columns and 'Product Name' in _storecounts_df.columns:
            df = pd.merge(
                df,
                _storecounts_df[['Distributor Location', 'Product Name', 'StoreCount_30days', 'StoreCount_60days', 'StoreCount_90days']],
                how='left',
                left_on=['Location', 'Product Name'],
                right_on=['Distributor Location', 'Product Name']
            )
            df.drop(columns=['Distributor Location'], inplace=True)
        else:
            print(f"Required columns missing in {os.path.basename(csv_path)} or storecounts; skipping storecounts merge")

    if run_eda_on_first and not _eda_run_for_first_report and DOWNLOAD_DIR and DASHBOARD_URL:
        _eda_run_for_first_report = True
        print(f"\n{'='*60}")
        print(f"Running EDA on merged data: {os.path.basename(csv_path)}")
        print(f"{'='*60}")

        temp_csv_path = os.path.join(DOWNLOAD_DIR, "temp_merged_for_eda.csv")
        df.to_csv(temp_csv_path, index=False)
        print(f"Saved merged data to: {temp_csv_path}")

        print("\n=== DEBUG: Column Names (After Merge) ===")
        print(f"Total columns: {len(df.columns)}")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        print("=== END Column Names ===\n")

        try:
            from run_auto_eda import run_eda_and_download_report
            from datetime import datetime
            import shutil
            print("Note: Dashboard may take 1-2 minutes to wake up if it's on Render free tier...")
            eda_pdf_path = run_eda_and_download_report(temp_csv_path, DASHBOARD_URL, DOWNLOAD_DIR)
            if eda_pdf_path and os.path.isfile(eda_pdf_path):
                today = datetime.now().strftime("%Y-%m-%d")
                target_eda_pdf_name = f"Report_{today}_EDA.pdf"
                target_eda_pdf_path = os.path.join(DOWNLOAD_DIR, target_eda_pdf_name)
                shutil.move(eda_pdf_path, target_eda_pdf_path)
                print(f"✓ EDA PDF created: {target_eda_pdf_path}")
            else:
                print("✗ EDA PDF file missing; continuing without it.")
        except Exception as e:
            print(f"✗ Failed to run EDA: {e}")
            print("  Continuing with PDF conversion...")
        finally:
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
        print(f"{'='*60}\n")

    if df.empty:
        raise ValueError(f"CSV file '{csv_path}' is empty after processing.")

    if not skip_location_total:
        if "Location" in df.columns and "Product Name" in df.columns:
            df["Location_shift"] = df["Location"].shift(1)
            new_location_mask = df["Location"] != df["Location_shift"]
            df.loc[new_location_mask, "Product Name"] = "Total"
            df = df.drop(columns=["Location_shift"])

    df = df.drop_duplicates()

    required_cols = {"Product Name", "On Floor Inventory (Cases)", "Location"}
    if required_cols.issubset(df.columns):
        df["On Floor Inventory (Cases)"] = pd.to_numeric(
            df["On Floor Inventory (Cases)"], errors="coerce"
        )
        zero_total_locations = df[
            (df["Product Name"] == "Total") &
            (df["On Floor Inventory (Cases)"] == 0.0)
        ]["Location"].unique()
        df = df[~df["Location"].isin(zero_total_locations)]
    else:
        print(f"Skipping zero-total filter for {os.path.basename(csv_path)} (missing required columns)")

    pdf_path = csv_path.replace(".csv", ".pdf")
    page_width, page_height = landscape(letter)
    pdf = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))

    cell_style = ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=7,
        leading=8,
        alignment=1,
        spaceAfter=0,
        spaceBefore=0,
    )

    data = []
    data.append([Paragraph(str(col), cell_style) for col in df.columns])
    for _, row in df.iterrows():
        data.append([Paragraph(str(cell), cell_style) for cell in row])

    col_widths = []
    for col in df.columns:
        max_len = max(df[col].astype(str).map(len).max(), len(col))
        col_widths.append(max_len * 6)

    total_width = sum(col_widths)
    available_width = page_width - 80
    if total_width > available_width:
        scale_factor = available_width / total_width
        col_widths = [w * scale_factor for w in col_widths]

    table = Table(data, repeatRows=1, colWidths=col_widths)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#000000")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    table.setStyle(style)
    pdf.build([table])
    print(f"Converted {os.path.basename(csv_path)} → {os.path.basename(pdf_path)}")
    return pdf_path

def split_and_convert_by_location(csv_path):
    LOCATION_ORDER = [
        "Charleston",
        "Columbia",
        "Greenville",
        "Myrtle",
        "Florence",
    ]

    def get_location_key(location):
        name = str(location)
        for i, keyword in enumerate(LOCATION_ORDER):
            if keyword in name:
                return i
        return len(LOCATION_ORDER)

    df = pd.read_csv(csv_path)

    if "Location" not in df.columns:
        raise ValueError(f"'Location' column not found in {csv_path}")

    # Rename the first row of each location group to Total and drop blank separator rows
    cleaned_groups = []
    for location, group in df.groupby("Location", sort=False):
        group = group.copy().reset_index(drop=True)
        group.at[0, "Product Name"] = "Total"
        group = group[group["Product Name"] != ""].copy()
        group = group[group["Product Name"].notna()].copy()
        cleaned_groups.append(group)

    df = pd.concat(cleaned_groups).reset_index(drop=True)

    if "Product Name" in df.columns:
        df = sort_by_product_order(df)
    else:
        print("Warning: 'Product Name' column not found; skipping custom sort.")

    base_dir = os.path.dirname(csv_path)
    pdf_paths = []

    sorted_locations = sorted(df["Location"].unique(), key=get_location_key)

    for location in sorted_locations:
        location_df = df[df["Location"] == location].copy()
        location_df = location_df.drop_duplicates(subset=["Product Name"])

        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in str(location)).strip()
        temp_csv = os.path.join(base_dir, f"_temp_consolidated_{safe_name}.csv")

        try:
            location_df.to_csv(temp_csv, index=False)
            pdf_path = csv_to_pdf(temp_csv, skip_location_total=True)
            if pdf_path and os.path.isfile(pdf_path):
                final_pdf = os.path.join(base_dir, f"Consolidated_{safe_name}.pdf")
                os.replace(pdf_path, final_pdf)
                pdf_paths.append(final_pdf)
                print(f"Created location PDF: {os.path.basename(final_pdf)}")
        except Exception as e:
            print(f"Failed to convert location '{location}': {e}")
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)

    return pdf_paths
