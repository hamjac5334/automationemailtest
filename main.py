#init everything
from dsd_downloader import download_report
from gmail_utils import gmail_authenticate, send_email
import os

USERNAME = os.environ["DSD_USERNAME"]
PASSWORD = os.environ["DSD_PASSWORD"]

print("Starting report downloads...")

#  Add your actual report URLs here
reports = [
    {"name": "Inventory_Report", "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835190"},
    {"name": "Sales_Report", "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835190"},
    {"name": "Delivery_Report", "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835190"},
    {"name": "Returns_Report", "url": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22835190"},
]

downloaded_files = []
for r in reports:
    for attempt in range(3):  # Retry up to 3 times
        try:
            path = download_report(USERNAME, PASSWORD, r["name"], r["url"])
            downloaded_files.append(path)
            break
        except Exception as e:
            sleep(5)

print("All reports downloaded successfully.")

# Authenticate Gmail
print("Authenticating Gmail...")
service = gmail_authenticate()

#mason.holland@hollandplace.net, chad.elkins@tapsandtables.net
recipients = "jackson@bogmayer.com"
send_email(
    service=service,
    sender="jackson@bogmayer.com",
    to=recipients,
    subject="Daily Report",
    attachment_path=downloaded_files
)
print("Email sent!")

