#init everything
from dsd_downloader import download_report
from gmail_utils import gmail_authenticate, send_email
from datetime import datetime
import os

USERNAME = os.environ["DSD_USERNAME"]
PASSWORD = os.environ["DSD_PASSWORD"]

# Define your reports here (url, original filename from site, new filename)
reports = [
    {
        "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835190",
        "original_filename": "Live_Inventory_Snapshot_automation_test.csv",
        "new_filename": f"Live_Inventory_{datetime.now().strftime('%Y-%m-%d')}.csv"
    },
    {
        "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22818254",
        "original_filename": "Live_Inventory_Snapshot_automation_test.csv",
        "new_filename": f"Test_Export_{datetime.now().strftime('%Y-%m-%d')}.csv"
    },
    # Add more reports as needed
]

print("Downloading reports...")
downloaded_files = []

for report in reports:
    path = download_report(
        USERNAME,
        PASSWORD,
        report["url"],
        report["original_filename"],
        report["new_filename"],
    )
    downloaded_files.append(path)
    print(f"Downloaded to {path}")

print("Sending email...")
service = gmail_authenticate()
recipients = "jackson@bogmayer.com"

send_email(
    service=service,
    sender="jackson@bogmayer.com",
    to=recipients,
    subject="Daily Reports",
    attachment_paths=downloaded_files
)
print("Email sent!")

