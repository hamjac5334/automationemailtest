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
# ,"mason.holland@hollandplace.net", "chad.elkins@tapsandtables.net"
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
        print(f"Failed to download {report_name}: {e}")

print("\nAll CSVs after download:")
for f in downloaded_files:
    print(f"  {f} (exists: {os.path.isfile(f) if f else 'N/A'})")

if len(downloaded_files) < len(REPORTS):
    print("Warning: Not all reports downloaded successfully.")

expected_storecounts = ['_5.csv', '_6.csv', '_7.csv']
storecount_files = [f for f in downloaded_files if any(f and f.endswith(s) for s in expected_storecounts)]
if len(storecount_files) == 3:
    merged_storecounts_df = storecounts.merge_three_storecounts_reports()
    combined_storecounts_path = os.path.join(storecounts.DOWNLOAD_DIR, "combined_storecounts.csv")
    merged_storecounts_df.to_csv(combined_storecounts_path, index=False)
    set_storecounts_path(combined_storecounts_path)
else:
    print("Warning: Missing one or more storecounts files; skipping merge.")

storecounts_30_csv = next((f for f in downloaded_files if f and f.endswith('_5.csv')), None)
storecounts_60_csv = next((f for f in downloaded_files if f and f.endswith('_6.csv')), None)
storecounts_90_csv = next((f for f in downloaded_files if f and f.endswith('_7.csv')), None)

pdf_files = []

# Convert main reports to PDF
for csv_path in downloaded_files[:4]:
    if csv_path and os.path.isfile(csv_path):
        try:
            pdf_path = csv_to_pdf(csv_path)
            print(f"Converted {csv_path} -> {pdf_path}, exists: {os.path.isfile(pdf_path) if pdf_path else 'N/A'}")
            if pdf_path and os.path.isfile(pdf_path):
                pdf_files.append(pdf_path)
            else:
                print(f"[WARN] PDF for {csv_path} missing after conversion!")
        except Exception as e:
            print(f"Failed to convert {csv_path} to PDF: {e}")

# Convert storecounts CSVs to PDF (if present)
for sc_csv in (storecounts_30_csv, storecounts_60_csv, storecounts_90_csv):
    if sc_csv and os.path.isfile(sc_csv):
        try:
            sc_pdf = csv_to_pdf(sc_csv)
            print(f"Converted {sc_csv} -> {sc_pdf}, exists: {os.path.isfile(sc_pdf) if sc_pdf else 'N/A'}")
            if sc_pdf and os.path.isfile(sc_pdf):
                pdf_files.append(sc_pdf)
            else:
                print(f"[WARN] Storecounts PDF for {sc_csv} missing after conversion!")
        except Exception as e:
            print(f"Failed to convert storecounts CSV {sc_csv} to PDF: {e}")

# Step 1: Send initial email with the 7 converted reports
try:
    valid_attachments = [f for f in pdf_files if os.path.isfile(f)]
    print("\nSending first email with initial reports:")
    for f in valid_attachments:
        print(f"  {f}")
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=", ".join(GMAIL_RECIPIENTS),
        subject="Automated DSD Reports - Initial",
        body="This is an automated email.\n\nAttached are the latest DSD reports.",
        attachments=valid_attachments
    )
    print("\nFirst email sent successfully.")
except Exception as e:
    print(f"\nFailed to send first email: {e}")

# Step 2: Clear directory to prepare for EDA PDF generation
print("Clearing directory for EDA report generation...")
for f in os.listdir(storecounts.DOWNLOAD_DIR):
    file_path = os.path.join(storecounts.DOWNLOAD_DIR, f)
    try:
        os.remove(file_path)
    except Exception as error:
        print(f"Failed to delete {file_path}: {error}")

# Step 3: Run EDA report and send it in a separate email
dashboard_url = "https://automatedanalytics.onrender.com/"
try:
    eda_pdf_path = run_eda_and_download_report(downloaded_files[1], dashboard_url, storecounts.DOWNLOAD_DIR)
    if eda_pdf_path and os.path.isfile(eda_pdf_path):
        print(f"EDA report generated: {eda_pdf_path}")
        send_email_with_attachments(
            sender=GMAIL_ADDRESS,
            to=", ".join(GMAIL_RECIPIENTS),
            subject="Automated DSD Report - EDA Analysis",
            body="This is an automated email.\n\nAttached is the EDA report.",
            attachments=[eda_pdf_path]
        )
        print("Second email with EDA sent successfully.")
    else:
        print("EDA report generation failed or timed out.")
except Exception as e:
    print(f"Failed during EDA report generation or email sending: {e}")
