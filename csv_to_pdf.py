import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

def csv_to_pdf(csv_path):
    """
    Converts a CSV file to a PDF table, fixing 'Product Name' for total rows,
    scaling to fit all columns, and keeping text neatly wrapped inside each cell.

    Before conversion, merges the corresponding storecounts file to add 'StoreCount' column.
    """
    df = pd.read_csv(csv_path)

    # Attempt to find the matching storecounts file
    base_path = os.path.splitext(csv_path)[0]
    storecounts_path = f"{base_path}_with_storecounts.csv"

    if os.path.exists(storecounts_path):
        storecounts_df = pd.read_csv(storecounts_path)

        # Rename for consistent column name to merge
        if 'Distributor Location' in storecounts_df.columns:
            storecounts_df = storecounts_df.rename(columns={'Distributor Location': 'Location'})

        # Merge storecounts into original df
        if 'Location' in df.columns and 'Product Name' in df.columns and \
           'Location' in storecounts_df.columns and 'Product Name' in storecounts_df.columns:
            df = pd.merge(df, storecounts_df[['Location', 'Product Name', 'StoreCount']],
                          on=['Location', 'Product Name'], how='left')
        else:
            print("Required columns for merging store counts not found in one or both DataFrames.")

    else:
        print(f"No matching storecounts file found for {csv_path}, skipping merge.")

    if df.empty:
        raise ValueError(f"CSV file '{csv_path}' is empty after processing.")

    if "Location" in df.columns and "Product Name" in df.columns:
        df["Location_shift"] = df["Location"].shift(1)
        new_location_mask = df["Location"] != df["Location_shift"]
        df.loc[new_location_mask, "Product Name"] = "Total"
        df = df.drop(columns=["Location_shift"])

    pdf_path = csv_path.replace(".csv", ".pdf")
    page_width, page_height = landscape(letter)
    pdf = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))

    cell_style = ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=7,
        leading=8,
        alignment=1,  # centered
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

    total_table_width = sum(col_widths)
    available_width = page_width - 80

    if total_table_width > available_width:
        scale_factor = available_width / total_table_width
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





