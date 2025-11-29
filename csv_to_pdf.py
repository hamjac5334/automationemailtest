import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

# Update this path to point to report 5 storecounts CSV
STORECOUNTS_PATH = None  
DOWNLOAD_DIR = None  # Will be set by main.py
DASHBOARD_URL = None  # Will be set by main.py

_storecounts_df = None
_eda_run_for_first_report = False  # Flag to ensure EDA only runs once

def set_storecounts_path(storecounts_path):
    global STORECOUNTS_PATH, _storecounts_df
    STORECOUNTS_PATH = storecounts_path
    if os.path.exists(storecounts_path):
        df = pd.read_csv(storecounts_path)
        _storecounts_df = df
        # If the storecounts file uses 'Distributor Location', keep that column
        # Don't rename here, merge uses right_on explicitly
    else:
        _storecounts_df = pd.DataFrame(columns=['Distributor Location', 'Product Name', 'StoreCount'])

def set_eda_config(download_dir, dashboard_url):
    """Set configuration for EDA dashboard"""
    global DOWNLOAD_DIR, DASHBOARD_URL
    DOWNLOAD_DIR = download_dir
    DASHBOARD_URL = dashboard_url

def csv_to_pdf(csv_path, run_eda_on_first=False):
    global _storecounts_df, _eda_run_for_first_report
    df = pd.read_csv(csv_path)

    # Only merge if storecounts DataFrame is loaded and not empty
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

    # Run EDA on the FIRST report AFTER merge but BEFORE PDF conversion
    if run_eda_on_first and not _eda_run_for_first_report and DOWNLOAD_DIR and DASHBOARD_URL:
        _eda_run_for_first_report = True  # Set flag so we only run once
        
        print(f"\n{'='*60}")
        print(f"Running EDA on merged data: {os.path.basename(csv_path)}")
        print(f"{'='*60}")
        
        # Debug: Print column names
        print("\n=== DEBUG: Column Names (After Merge) ===")
        print(f"Total columns: {len(df.columns)}")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        print("=== END Column Names ===\n")
        
        # Save merged dataframe to temporary CSV for EDA
        temp_csv_path = os.path.join(DOWNLOAD_DIR, "temp_merged_for_eda.csv")
        df.to_csv(temp_csv_path, index=False)
        print(f"Saved merged data to: {temp_csv_path}")
        
        # Run EDA
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
            # Clean up temp CSV
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
        
        print(f"{'='*60}\n")

    if df.empty:
        raise ValueError(f"CSV file '{csv_path}' is empty after processing.")

    if "Location" in df.columns and "Product Name" in df.columns:
        df["Location_shift"] = df["Location"].shift(1)
        new_location_mask = df["Location"] != df["Location_shift"]
        df.loc[new_location_mask, "Product Name"] = "Total"
        df = df.drop(columns=["Location_shift"])

    df = df.drop_duplicates()

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

    pdf.build([table])

    print(f"Converted {os.path.basename(csv_path)} → {os.path.basename(pdf_path)}")
    return pdf_path
