# csv_to_pdf.py
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

def csv_to_pdf(csv_path):
    """
    Converts a CSV file to a PDF table and saves it in the same directory.
    Returns the path to the generated PDF.
    """
    df = pd.read_csv(csv_path)

    if df.empty:
        raise ValueError(f"CSV file '{csv_path}' is empty.")

    data = [df.columns.tolist()] + df.values.tolist()

    pdf_path = csv_path.replace(".csv", ".pdf")
    pdf = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))

    # --- Auto-adjust column widths ---
    col_widths = []
    for col in df.columns:
        max_len = max(df[col].astype(str).map(len).max(), len(col))
        # Scale width proportional to length, but keep within a reasonable range
        width = max(60, min(max_len * 7, 200))
        col_widths.append(width)

    table = Table(data, repeatRows=1, colWidths=col_widths)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#333333")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ])
    table.setStyle(style)

    pdf.build([table])

    print(f"Converted {os.path.basename(csv_path)} → {os.path.basename(pdf_path)}")
    return pdf_path

