#mason.holland@hollandplace.net, chad.elkins@tapsandtables.net

#init everything
from dsd_downloader import download_reports
from gmail_utils import gmail_authenticate, send_email
import os

USERNAME = os.environ["DSD_USERNAME"]
PASSWORD = os.environ["DSD_PASSWORD"]

print("Starting report downloads...")

# Define the reports to download
reports = [
    {"name": "Inventory_Report", "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835190"},
    {"name": "Sales_Report", "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835191"},
    {"name": "Delivery_Report", "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835192"},
    {"name": "Returns_Report", "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835193"},
]

# Download all reports in a single browser session
downloaded_files = download_reports(USERNAME, PASSWORD, reports)

print("All reports downloaded successfully.")

# Authenticate Gmail
print("Authenticating Gmail...")
service = gmail_authenticate()

recipients = "jackson@bogmayer.com"
send_email(
    service=service,
    sender="jackson@bogmayer.com",
    to=recipients,
    subject="Daily Report",
    attachment_paths=downloaded_files
)
print("Email sent!")
