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

# Download CSV reports
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

# Merge Storecounts reports CSVs and set path for merging if all exist
expected_storecounts_suffixes = ['_5.csv', '_6.csv', '_7.csv']
storecount_files = [f for f in downloaded_files if any(f and f.endswith(s) for s in expected_storecounts_suffixes)]
if len(storecount_files) == 3:
    merged_storecounts_df = storecounts.merge_three_storecounts_reports()
    combined_storecounts_path = os.path.join(download_dir, "combined_storecounts.csv")
    merged_storecounts_df.to_csv(combined_storecounts_path, index=False)
    set_storecounts_path(combined_storecounts_path)
else:
    print("Warning: Missing one or more storecounts files; skipping merge.")

# Identify storecounts CSV files
storecounts_csvs = {
    '30': next((f for f in downloaded_files if f.endswith('_5.csv')), None),
    '60': next((f for f in downloaded_files if f.endswith('_6.csv')), None),
    '90': next((f for f in downloaded_files if f.endswith('_7.csv')), None),
}

pdf_files = []

# Convert FIRST 4 CSVs (main product reports) to PDFs and collect absolute paths
for csv_path in downloaded_files[:4]:
    if csv_path and os.path.isfile(csv_path):
        try:
            pdf_path = csv_to_pdf(csv_path)
            abs_pdf_path = os.path.abspath(pdf_path) if pdf_path else None
            if abs_pdf_path and os.path.isfile(abs_pdf_path):
                print(f"Appended PDF: {abs_pdf_path}")
                pdf_files.append(abs_pdf_path)
            else:
                print(f"[WARN] PDF missing after conversion for {csv_path}")
        except Exception as e:
            print(f"Failed to convert {csv_path} to PDF: {e}")

# Convert Storecounts CSVs if exist and append PDFs
for key in ['30', '60', '90']:
    sc_csv = storecounts_csvs[key]
    if sc_csv and os.path.isfile(sc_csv):
        try:
            sc_pdf = csv_to_pdf(sc_csv)
            abs_sc_pdf = os.path.abspath(sc_pdf) if sc_pdf else None
            if abs_sc_pdf and os.path.isfile(abs_sc_pdf):
                print(f"Appended Storecounts {key}-day PDF: {abs_sc_pdf}")
                pdf_files.append(abs_sc_pdf)
            else:
                print(f"[WARN] Storecounts {key}-day PDF missing after conversion.")
        except Exception as e:
            print(f"Failed to convert storecounts {key}-day CSV to PDF: {e}")

# Run EDA dashboard generation and attach the PDF at last
dashboard_url = "https://automatedanalytics.onrender.com/"
if (len(downloaded_files) > 1) and downloaded_files[1] and os.path.isfile(downloaded_files[1]):
    print(f"Preparing EDA analysis for {downloaded_files[1]}")
    try:
        eda_pdf_path = run_eda_and_download_report(downloaded_files[1], dashboard_url, download_dir)
        if eda_pdf_path and os.path.isfile(eda_pdf_path):
            today = datetime.now().strftime("%Y-%m-%d")
            target_eda_pdf_path = os.path.abspath(os.path.join(download_dir, f"Report_{today}_EDA.pdf"))
            # Only move if different paths
            if os.path.abspath(eda_pdf_path) != target_eda_pdf_path:
                shutil.move(eda_pdf_path, target_eda_pdf_path)
            print(f"Appended EDA PDF: {target_eda_pdf_path}")
            pdf_files.append(target_eda_pdf_path)
        else:
            print("EDA PDF missing; not attached.")
    except Exception as e:
        print(f"Failed to get EDA PDF: {e}")
else:
    print("No valid target CSV for dashboard EDA; skipping.")

# Print final files for emailing
print("\nFinal list of PDFs for email attachment:")
for f in pdf_files:
    print(f"  {f} (exists: {os.path.isfile(f)})")

valid_attachments = [f for f in pdf_files if os.path.isfile(f)]

if not valid_attachments:
    print("ERROR: No PDFs to attach! Email will not be sent.")
else:
    print(f"Sending email with {len(valid_attachments)} attachments.")

    try:
        send_email_with_attachments(
            sender=GMAIL_ADDRESS,
            to=", ".join(GMAIL_RECIPIENTS),
            subject="Automated DSD Reports",
            body="""This is an automated email.

Attached are the latest DSD reports as PDFs.""" ,
            attachments=valid_attachments
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
