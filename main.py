#init everything
from dsd_downloader import download_reports
from gmail_utils import gmail_authenticate, send_email
import os

USERNAME = os.environ["DSD_USERNAME"]
PASSWORD = os.environ["DSD_PASSWORD"]

print("Downloading reports...")

report_links = [
    ("https://dsdlink.com/Home?DashboardID=100120&ReportID=22835190", "InventoryReport"),
    ("https://dsdlink.com/Home?DashboardID=100120&ReportID=22818254", "TestReport")
]

report_paths = download_reports(USERNAME, PASSWORD, report_links)
print(f"Downloaded reports: {report_paths}")

print("Sending email...")
service = gmail_authenticate()
send_email(
    service,
    sender=os.environ["GMAIL_ADDRESS"],
    to=os.environ["GMAIL_RECIPIENT"],
    subject="Daily Automated Reports",
    body_text="Attached are today's reports.",
    attachment_paths=report_paths
)
print("Email sent!")
