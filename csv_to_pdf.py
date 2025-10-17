import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

def csv_to_pdf(csv_path):
    """
    Converts a CSV file to a PDF table, scales to fit all columns,
    and ensures all text stays inside each cell (wrapped neatly).
    """
    df = pd.read_csv(csv_path)

    if df.empty:
        raise ValueError(f"CSV file '{csv_path}' is empty.")

    pdf_path = csv_path.replace(".csv", ".pdf")
    page_width, page_height = landscape(letter)
    pdf = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))

    # Paragraph style for cell wrapping
    cell_style = ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=7,
        leading=8,
        alignment=1,  # center
        spaceAfter=0,
        spaceBefore=0,
    )

    # Convert all data cells to Paragraphs (for word wrap)
    data = []
    data.append([Paragraph(str(col), cell_style) for col in df.columns])
    for _, row in df.iterrows():
        data.append([Paragraph(str(cell), cell_style) for cell in row])

    # Estimate column widths based on content length
    col_widths = []
    for col in df.columns:
        max_len = max(df[col].astype(str).map(len).max(), len(col))
        col_widths.append(max_len * 6)

    total_table_width = sum(col_widths)
    available_width = page_width - 80  # margin space

    # Scale down proportionally if needed
    if total_table_width > available_width:
        scale_factor = available_width / total_table_width
        col_widths = [w * scale_factor for w in col_widths]

    table = Table(data, repeatRows=1, colWidths=col_widths)

    # Define table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    table.setStyle(style)

    pdf.build([table])

    print(f"Converted {os.path.basename(csv_path)} → {os.path.basename(pdf_path)}")
    return pdf_path



