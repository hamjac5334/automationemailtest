#init everything
import os
from dsd_downloader import download_report
from gmail_utils import send_email_with_attachments

# Credentials from GitHub secrets or environment variables
USERNAME = os.environ.get("DSD_USERNAME")
PASSWORD = os.environ.get("DSD_PASSWORD")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_RECIPIENT = "jackson@bogmayer.com"  # directly send to this email

# List of report URLs and names (optional friendly names)
REPORTS = [
    ("Sales Summary", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972383"),
    ("Brand Performance", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972382"),
    ("Weekly Volume", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972378"),
    ("Retail Sales", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972365")
]

# Download reports
downloaded_files = []
print("Downloading reports...\n")
for i, (report_name, url) in enumerate(REPORTS, start=1):
    try:
        print(f"Downloading {report_name}...")
        path = download_report(USERNAME, PASSWORD, url, report_number=i)
        downloaded_files.append(path)
    except Exception as e:
        print(f"⚠️ Failed to download {report_name}: {e}")

if not downloaded_files:
    print("❌ No reports downloaded. Exiting.")
    exit(1)

# Send email with all downloaded reports attached
subject = "Automated DSD Reports"
body = "Hi,\n\nAttached are the latest DSD reports.\n\nBest regards,\nAutomated Report Bot"

try:
    send_email_with_attachments(
        service=None,  # update if you initialize the Gmail API service in gmail_utils
        sender=GMAIL_ADDRESS,
        to=GMAIL_RECIPIENT,
        subject=subject,
        body=body,
        attachments=downloaded_files
    )
    print("\n✅ Email sent successfully.")
except Exception as e:
    print(f"\n❌ Failed to send email: {e}")
