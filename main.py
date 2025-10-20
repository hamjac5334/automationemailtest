import os
from dsd_downloader import download_report
from gmail_utils import send_email_with_attachments
from csv_to_pdf import csv_to_pdf  # <-- NEW import

USERNAME = os.environ.get("DSD_USERNAME")
PASSWORD = os.environ.get("DSD_PASSWORD")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
#,"mason.holland@hollandplace.net", "chad.elkins@tapsandtables.net"
GMAIL_RECIPIENTS = ["jackson@bogmayer.com","mason.holland@hollandplace.net", "chad.elkins@tapsandtables.net]

REPORTS = [
    ("Sales Summary", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972383"),
    ("Brand Performance", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972382"),
    ("Weekly Volume", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972378"),
    ("Retail Sales", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972365")
]

print("Downloading reports...\n")
downloaded_files = []
for i, (report_name, url) in enumerate(REPORTS, start=1):
    try:
        print(f"Downloading {report_name}...")
        path = download_report(USERNAME, PASSWORD, url, report_number=i)
        downloaded_files.append(path)
    except Exception as e:
        print(f" Failed to download {report_name}: {e}")

if not downloaded_files:
    print(" No reports downloaded. Exiting.")
    exit(1)

# ✅ Convert CSVs → PDFs
pdf_files = []
for csv_path in downloaded_files:
    try:
        pdf_path = csv_to_pdf(csv_path)
        pdf_files.append(pdf_path)
    except Exception as e:
        print(f"Failed to convert {csv_path} to PDF: {e}")

if not pdf_files:
    print("No PDFs created. Exiting.")
    exit(1)

to_header = ", ".join(GMAIL_RECIPIENTS)

subject = "Automated DSD Reports"
body = """This is an automated email test.

Attached are the latest DSD reports as PDFs. 
These are live inventory snapshots of:
1. SCP/KW in SC 
2. SCP in GA
3. Tryon
4. Cavalier
"""

try:
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=to_header,
        subject=subject,
        body=body,
        attachments=pdf_files   # <-- Send PDFs instead of CSVs
    )
    print("\nEmail sent successfully.")
except Exception as e:
    print(f"\n Failed to send email: {e}")

