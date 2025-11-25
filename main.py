import os
from dsd_downloader import download_report
from gmail_utils import send_email_with_attachments
from csv_to_pdf import csv_to_pdf, set_storecounts_path
from run_auto_eda import run_eda_and_download_report
from datetime import datetime
import shutil
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

# Merge storecounts only if all expected files exist
expected_storecounts = ['_5.csv', '_6.csv', '_7.csv']
storecount_files = [f for f in downloaded_files if any(f.endswith(s) for s in expected_storecounts)]
if len(storecount_files) == 3:
    merged_storecounts_df = storecounts.merge_three_storecounts_reports()
    combined_storecounts_path = os.path.join(storecounts.DOWNLOAD_DIR, "combined_storecounts.csv")
    merged_storecounts_df.to_csv(combined_storecounts_path, index=False)
    set_storecounts_path(combined_storecounts_path)
else:
    print("Warning: Missing one or more storecounts files; skipping merge.")

# Find storecounts CSVs safely
storecounts_30_csv = next((f for f in downloaded_files if f.endswith('_5.csv')), None)
storecounts_60_csv = next((f for f in downloaded_files if f.endswith('_6.csv')), None)
storecounts_90_csv = next((f for f in downloaded_files if f.endswith('_7.csv')), None)

if not (storecounts_30_csv and storecounts_60_csv and storecounts_90_csv):
    print("Warning: One or more storecounts reports failed to download.")

pdf_files = []
# Convert main product reports (1-4)
for csv_path in downloaded_files[:4]:
    if csv_path and os.path.isfile(csv_path):
        try:
            pdf_files.append(csv_to_pdf(csv_path))
        except Exception as e:
            print(f"Failed to convert {csv_path} to PDF: {e}")

# Convert storecounts CSVs 30 and 60 days
pdf_sc30 = pdf_sc60 = pdf_sc90 = None

if storecounts_30_csv and os.path.isfile(storecounts_30_csv):
    try:
        pdf_sc30 = csv_to_pdf(storecounts_30_csv)
        pdf_files.append(pdf_sc30)
    except Exception as e:
        print(f"Failed to convert storecounts 30 CSV to PDF: {e}")

if storecounts_60_csv and os.path.isfile(storecounts_60_csv):
    try:
        pdf_sc60 = csv_to_pdf(storecounts_60_csv)
        pdf_files.append(pdf_sc60)
    except Exception as e:
        print(f"Failed to convert storecounts 60 CSV to PDF: {e}")

if storecounts_90_csv and os.path.isfile(storecounts_90_csv):
    try:
        pdf_sc90 = csv_to_pdf(storecounts_90_csv)
        pdf_files.append(pdf_sc90)
    except Exception as e:
        print("90-day storecounts CSV file missing; skipping its PDF attachment.")

# Run EDA only if valid target CSV exists
dashboard_url = "https://automatedanalytics.onrender.com/"
if downloaded_files[1] and os.path.isfile(downloaded_files[1]):
    try:
        eda_pdf_path = run_eda_and_download_report(downloaded_files[1], dashboard_url, storecounts.DOWNLOAD_DIR)
        pdf_files.append(eda_pdf_path)
    except Exception as e:
        print(f"Failed to run dashboard analysis: {e}")
else:
    print("No valid target CSV for dashboard EDA; skipping.")

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
5. List of Retail Stores
""",
        attachments=[f for f in pdf_files if f]
    )
    print("\nEmail sent successfully.")
except Exception as e:
    print(f"\nFailed to send email: {e}")
