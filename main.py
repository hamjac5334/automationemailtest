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

# Convert all (1-7) CSVs to PDF, collect absolute PDF paths
pdf_files = []
for csv_path in downloaded_files:
    if csv_path and os.path.isfile(csv_path):
        try:
            pdf_path = csv_to_pdf(csv_path)
            abs_pdf_path = os.path.abspath(pdf_path) if pdf_path else None
            print(f"Converted {csv_path} -> {abs_pdf_path}, exists: {os.path.isfile(abs_pdf_path) if abs_pdf_path else 'N/A'}")
            if abs_pdf_path and os.path.isfile(abs_pdf_path):
                pdf_files.append(abs_pdf_path)
            else:
                print(f"[WARN] PDF for {csv_path} missing after conversion!")
        except Exception as e:
            print(f"Failed to convert {csv_path} to PDF: {e}")

# ----- Add EDA dashboard PDF -----
dashboard_url = "https://automatedanalytics.onrender.com/"
if downloaded_files[1] and os.path.isfile(downloaded_files[1]):
    print(f"Preparing EDA analysis for {downloaded_files[1]}")
    try:
        eda_pdf_path = run_eda_and_download_report(downloaded_files[1], dashboard_url, download_dir)
        if eda_pdf_path and os.path.isfile(eda_pdf_path):
            today = datetime.now().strftime("%Y-%m-%d")
            target_eda_pdf_path = os.path.abspath(os.path.join(download_dir, f"Report_{today}_EDA.pdf"))
            if not os.path.samefile(eda_pdf_path, target_eda_pdf_path):
                shutil.move(eda_pdf_path, target_eda_pdf_path)
            pdf_files.append(target_eda_pdf_path)
            print(f"Appended EDA PDF: {target_eda_pdf_path}")
        else:
            print("EDA PDF file missing; skipping attachment.")
    except Exception as e:
        print(f"Failed to run dashboard analysis: {e}")
else:
    print("No valid target CSV for dashboard EDA; skipping.")

print("\n\nDownload directory (should have PDFs):")
for item in os.listdir(download_dir):
    if item.lower().endswith('.pdf'):
        print("  ", item)
print("\nFinal PDF list to attach:")
for f in pdf_files:
    print(f"  {f} (exists: {os.path.isfile(f)})")

attachments = [f for f in pdf_files if os.path.isfile(f)]
print(f"\nFinal attachments ({len(attachments)}):")
for f in attachments:
    print("  ", f)

if not attachments:
    print("ERROR: No PDFs found for attachment. Check conversion output directory and email logic.")
else:
    try:
        send_email_with_attachments(
            sender=GMAIL_ADDRESS,
            to=", ".join(GMAIL_RECIPIENTS),
            subject="Automated DSD Reports",
            body="Automated PDF DSD reports attached.",
            attachments=attachments
        )
        print("\nEmail sent successfully.")
    except Exception as e:
        print(f"\nFailed to send email: {e}")
