import os
from dsd_downloader import download_report
from gmail_utils import send_email_with_attachments
from csv_to_pdf import csv_to_pdf, set_storecounts_path
import storecounts

USERNAME = os.environ.get("DSD_USERNAME")
PASSWORD = os.environ.get("DSD_PASSWORD")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
#,"mason.holland@hollandplace.net", "chad.elkins@tapsandtables.net"
GMAIL_RECIPIENTS = ["jackson@bogmayer.com"]

REPORTS = [
    ("Sales Summary", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972383"),
    ("Brand Performance", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972382"),
    ("Weekly Volume", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972378"),
    ("Retail Sales", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972365"),
    ("Store Counts 30 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23124246"),
    ("Store Counts 60 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23153930"),  
    ("Store Counts 90 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23157734")
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

if len(downloaded_files) < len(REPORTS):
    print("Warning: Not all reports downloaded successfully.")

# Merge the three storecounts reports (reports 5, 6, 7)
merged_storecounts_df = storecounts.merge_three_storecounts_reports()

combined_storecounts_path = os.path.join(storecounts.DOWNLOAD_DIR, "combined_storecounts.csv")
merged_storecounts_df.to_csv(combined_storecounts_path, index=False)

set_storecounts_path(combined_storecounts_path)

pdf_files = []
# Convert main product reports (1-4)
for csv_path in downloaded_files[:4]:
    try:
        pdf_files.append(csv_to_pdf(csv_path))
    except Exception as e:
        print(f"Failed to convert {csv_path} to PDF: {e}")

# Find storecounts CSVs dynamically by report IDs in paths
storecounts_30_csv = next((f for f in downloaded_files if "23124246" in f), None)
storecounts_60_csv = next((f for f in downloaded_files if "23153930" in f), None)
storecounts_90_csv = next((f for f in downloaded_files if "23157734" in f), None)

if not (storecounts_30_csv and storecounts_60_csv and storecounts_90_csv):
    print("Error: One or more storecounts reports failed to download.")
else:
    try:
        pdf_sc30 = csv_to_pdf(storecounts_30_csv)
        pdf_sc60 = csv_to_pdf(storecounts_60_csv)
        pdf_sc90 = csv_to_pdf(storecounts_90_csv)
        pdf_files.extend([pdf_sc30, pdf_sc60, pdf_sc90])
    except Exception as e:
        print(f"Failed to convert individual storecounts CSVs to PDFs: {e}")

try:
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=", ".join(GMAIL_RECIPIENTS),
        subject="Automated DSD Reports",
        body="""This is an automated email test.

Attached are the latest DSD reports as PDFs:
1. SCP/KW in SC
2. SCP in GA
3. Tryon
4. Cavalier
""",
        attachments=pdf_files
    )
    print("\nEmail sent successfully.")
except Exception as e:
    print(f"\nFailed to send email: {e}")
