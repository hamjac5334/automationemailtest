#init everything
import os
import time
from pdf_downloader import download_report_pdf
from gmail_utils import send_email_with_attachments

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

downloaded_files = []
for i, (report_name, url) in enumerate(REPORTS, start=1):
    print(f"Downloading {report_name} as PDF...")
    path = download_report_pdf(USERNAME, PASSWORD, url, report_number=i)
    if path:
        safe_name = report_name.replace(" ", "_")
        new_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}_{time.strftime('%Y-%m-%d')}.pdf")
        os.rename(path, new_path)
        downloaded_files.append(new_path)
        print(f"Saved {report_name} to {new_path}")
    else:
        print(f"Failed to download {report_name}.")

if not downloaded_files:
    print("No reports downloaded. Exiting.")
    exit(1)

subject = "Automated DSD Reports"
body = """This is an automated email.

Attached are the latest DSD reports with live inventory snapshots of:
1. SCP/KW in SC 
2. SCP in GA
3. Tryon
4. Cavalier
"""

to_header = ", ".join(GMAIL_RECIPIENTS)

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
