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

download_dir = storecounts.DOWNLOAD_DIR
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

merged_storecounts_df = storecounts.merge_three_storecounts_reports()
combined_storecounts_path = os.path.join(download_dir, "combined_storecounts.csv")
merged_storecounts_df.to_csv(combined_storecounts_path, index=False)
set_storecounts_path(combined_storecounts_path)

# Find storecounts CSVs
storecounts_30_csv = next((f for f in downloaded_files if f.endswith('_5.csv')), None)
storecounts_60_csv = next((f for f in downloaded_files if f.endswith('_6.csv')), None)
storecounts_90_csv = next((f for f in downloaded_files if f.endswith('_7.csv')), None)

if not (storecounts_30_csv and storecounts_60_csv and storecounts_90_csv):
    print("Error: One or more storecounts reports failed to download.")

pdf_files = []
# Convert product reports (1–4)
for csv_path in downloaded_files[:4]:
    try:
        pdf = csv_to_pdf(csv_path)
        if pdf and os.path.isfile(pdf):
            pdf_files.append(os.path.abspath(pdf))
    except Exception as e:
        print(f"Failed to convert {csv_path} to PDF: {e}")

# Storecounts PDFs
for sc_csv in [storecounts_30_csv, storecounts_60_csv, storecounts_90_csv]:
    if sc_csv and os.path.isfile(sc_csv):
        try:
            sc_pdf = csv_to_pdf(sc_csv)
            if sc_pdf and os.path.isfile(sc_pdf):
                pdf_files.append(os.path.abspath(sc_pdf))
        except Exception as e:
            print(f"Failed to convert {sc_csv} to PDF: {e}")

# === EDA report (dashboard automation) appended ===
dashboard_url = "https://automatedanalytics.onrender.com/"
if downloaded_files[1] and os.path.isfile(downloaded_files[1]):
    print(f"Preparing EDA analysis for {downloaded_files[1]}")
    try:
        eda_pdf_path = run_eda_and_download_report(downloaded_files[1], dashboard_url, download_dir)
        print(f"EDA output: {eda_pdf_path} (exists: {os.path.isfile(eda_pdf_path) if eda_pdf_path else 'N/A'})")
        if eda_pdf_path and os.path.isfile(eda_pdf_path):
            today = datetime.now().strftime("%Y-%m-%d")
            target_eda_pdf_path = os.path.abspath(os.path.join(download_dir, f"Report_{today}_EDA.pdf"))
            if os.path.abspath(eda_pdf_path) != target_eda_pdf_path:
                shutil.move(eda_pdf_path, target_eda_pdf_path)
            pdf_files.append(target_eda_pdf_path)
            print(f"Appended EDA PDF: {target_eda_pdf_path}")
        else:
            print("EDA PDF missing, not attached.")
    except Exception as e:
        print(f"Failed to get EDA PDF: {e}")

print("\nFinal list of PDFs to attach:")
for f in pdf_files:
    print(f"  {f} (exists: {os.path.isfile(f)})")

try:
    attachments = [f for f in pdf_files if os.path.isfile(f)]
    if not attachments:
        print("\nERROR: No PDFs found to attach. Exiting without email.")
    else:
        send_email_with_attachments(
            sender=GMAIL_ADDRESS,
            to=", ".join(GMAIL_RECIPIENTS),
            subject="Automated DSD Reports",
            body="Automated DSD PDF report bundle.",
            attachments=attachments
        )
        print("\nEmail sent successfully with all reports and EDA report attached.")
except Exception as e:
    print(f"\nFailed to send email: {e}")
