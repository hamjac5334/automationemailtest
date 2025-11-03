import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

# Update this path to point to report 5 storecounts CSV
STORECOUNTS_PATH = None  

_storecounts_df = None

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

def csv_to_pdf(csv_path):
    global _storecounts_df
    df = pd.read_csv(csv_path)

    # Only merge if storecounts DataFrame is loaded and not empty
    if _storecounts_df is not None and not _storecounts_df.empty:
        if 'Location' in df.columns and 'Product Name' in df.columns and \
           'Distributor Location' in _storecounts_df.columns and 'Product Name' in _storecounts_df.columns:
           
            df = pd.merge(
                df,
                _storecounts_df[['Distributor Location', 'Product Name', 'StoreCount']],
                how='left',
                left_on=['Location', 'Product Name'],
                right_on=['Distributor Location', 'Product Name']
            )
            # Drop the redundant column after merge
            df.drop(columns=['Distributor Location'], inplace=True)

            #df = df.drop_duplicates()
        else:
            print(f"Required columns missing in {os.path.basename(csv_path)} or storecounts; skipping storecounts merge")

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
