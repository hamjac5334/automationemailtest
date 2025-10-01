#init everything
from dsd_downloader import download_report
from gmail_utils import gmail_authenticate, send_email
import os

USERNAME = os.environ["DSD_USERNAME"]
PASSWORD = os.environ["DSD_PASSWORD"]

print("Downloading report...")
report_path = download_report(USERNAME, PASSWORD)
print(f"Downloaded report to {report_path}")

print("Sending email...")
service = gmail_authenticate()
send_email(
    service,
    "me",  # uses the Gmail account from token.json
    "Automated Report",
    "Here is the latest report.",
    report_path
)
print("Email sent!")
