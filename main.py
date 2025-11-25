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

EDA_DOWNLOAD_DIR = os.path.join(storecounts.DOWNLOAD_DIR, "EDA_Downloads")
os.makedirs(EDA_DOWNLOAD_DIR, exist_ok=True)

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

# Run EDA report (dashboard automation) in separate download dir and append its PDF
dashboard_url = "https://automatedanalytics.onrender.com/"
if (len(downloaded_files) > 1) and downloaded_files[1] and os.path.isfile(downloaded_files[1]):
    print(f"Preparing EDA analysis for {downloaded_files[1]}")
    try:
        eda_pdf_path = run_eda_and_download_report(downloaded_files[1], dashboard_url, EDA_DOWNLOAD_DIR)
        print(f"EDA output: {eda_pdf_path} (exists: {os.path.isfile(eda_pdf_path) if eda_pdf_path else 'N/A'})")
        if eda_pdf_path and os.path.isfile(eda_pdf_path):
            today = datetime.now().strftime("%Y-%m-%d")
            target_eda_pdf_name = f"Report_{today}_EDA.pdf"
            target_eda_pdf_path = os.path.join(storecounts.DOWNLOAD_DIR, target_eda_pdf_name)
            shutil.move(eda_pdf_path, target_eda_pdf_path)
            pdf_files.append(target_eda_pdf_path)
            print(f"Appended EDA PDF: {target_eda_pdf_path}")
        else:
            print("EDA PDF file missing; using fallback copy for attachment.")
            if pdf_files:
                today = datetime.now().strftime("%Y-%m-%d")
                target_eda_pdf_name = f"Report_{today}_EDA.pdf"
                target_eda_pdf_path = os.path.join(storecounts.DOWNLOAD_DIR, target_eda_pdf_name)
                shutil.copy(pdf_files[1], target_eda_pdf_path)  # copy Brand Performance PDF as fallback
                pdf_files.append(target_eda_pdf_path)
                print(f"[FALLBACK] Appended fallback EDA PDF: {target_eda_pdf_path}")
        
            except Exception as e:
                print(f"Failed to run dashboard analysis: {e}")
        else:
            print("No valid target CSV for dashboard EDA; skipping.")

print("\nFinal list of PDFs to attach:")
for f in pdf_files:
    print(f"  {f} (exists: {os.path.isfile(f)})")

try:
    valid_attachments = [f for f in pdf_files if os.path.isfile(f)]
    print("\nSending email with these attachments:")
    for f in valid_attachments:
        print(f"  {f}")
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=", ".join(GMAIL_RECIPIENTS),
        subject="Automated DSD Reports",
        body="""This is an automated email.

Attached are the latest DSD reports as PDFs:
1. SCP/KW in SC
2. SCP in GA
3. Tryon
4. Cavalier
5. List of Retail Stores
""",
        attachments=valid_attachments
    )
    print("\nEmail sent successfully.")
except Exception as e:
    print(f"\nFailed to send email: {e}")
