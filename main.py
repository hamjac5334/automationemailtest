#init everything
# main.py
import os
import time
import shutil
from pdf_downloader import download_report_pdf
from gmail_utils import send_email_with_attachments

# ----------------------------
# Configuration
# ----------------------------
USERNAME = os.environ.get("DSD_USERNAME")
PASSWORD = os.environ.get("DSD_PASSWORD")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_RECIPIENTS = ["jackson@bogmayer.com"]

REPORTS = [
    ("Sales Summary", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972383"),
    ("Brand Performance", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972382"),
    ("Weekly Volume", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972378"),
    ("Retail Sales", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972365")
]

DOWNLOAD_DIR = os.path.abspath("AutomatedEmailData")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Chrome default download folder (used by kiosk print)
CHROME_DEFAULT_DOWNLOAD = os.path.join(os.path.expanduser("~"), "Downloads")

# ----------------------------
# Helper function
# ----------------------------
def wait_for_pdf(filename_prefix, timeout=30):
    """Wait for PDF with given prefix to appear in Chrome download folder"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        for fname in os.listdir(CHROME_DEFAULT_DOWNLOAD):
            if fname.startswith(filename_prefix) and fname.lower().endswith(".pdf"):
                return os.path.join(CHROME_DEFAULT_DOWNLOAD, fname)
        time.sleep(1)
    return None

# ----------------------------
# Download PDFs
# ----------------------------
downloaded_files = []

for i, (report_name, url) in enumerate(REPORTS, start=1):
    print(f"Downloading {report_name} as PDF...")
    # Use pdf_downloader (kiosk print)
    download_report_pdf(USERNAME, PASSWORD, url, report_number=i)

    # Wait for PDF to appear
    prefix = f"Report_{time.strftime('%Y-%m-%d')}_{i}"
    pdf_path = wait_for_pdf(prefix, timeout=60)

    if pdf_path and os.path.exists(pdf_path):
        # Rename PDF to friendly name
        safe_name = report_name.replace(" ", "_")
        new_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}_{time.strftime('%Y-%m-%d')}.pdf")
        shutil.move(pdf_path, new_path)
        downloaded_files.append(new_path)
        print(f"Saved {report_name} to {new_path}")
    else:
        print(f"Failed to download {report_name}.")

if not downloaded_files:
    print("No reports downloaded. Exiting.")
    exit(1)

# ----------------------------
# Prepare email
# ----------------------------
to_header = ", ".join(GMAIL_RECIPIENTS)
subject = "Automated DSD Reports"
body = """This is an automated email.

Attached are the latest DSD reports with live inventory snapshots of:
1. SCP/KW in SC 
2. SCP in GA
3. Tryon
4. Cavalier
"""

# ----------------------------
# Send email
# ----------------------------
try:
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=to_header,
        subject=subject,
        body=body,
        attachments=downloaded_files
    )
    print("\nEmail sent successfully.")
except Exception as e:
    print(f"\nFailed to send email: {e}")
