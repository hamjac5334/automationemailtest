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
    # Load CSV
    df = pd.read_csv(csv_path)

    # Handle empty or invalid CSVs
    if df.empty:
        raise ValueError(f"CSV file '{csv_path}' is empty.")

    # Convert to list of lists
    data = [df.columns.tolist()] + df.values.tolist()

    # Build output PDF path
    pdf_path = csv_path.replace(".csv", ".pdf")

    # Create a PDF (landscape layout helps wide tables)
    pdf = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))

    # Create table
    table = Table(data, repeatRows=1)

    # Table styling
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#333333")),  # Header background
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),               # Header text color
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey])
    ])
    table.setStyle(style)

    # Build the PDF
    pdf.build([table])

    print(f"Converted {os.path.basename(csv_path)} → {os.path.basename(pdf_path)}")
    return pdf_path
