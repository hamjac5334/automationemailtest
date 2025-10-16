#init everything
from dsd_downloader import download_report
from gmail_utils import gmail_authenticate, send_email_with_attachments
import os

USERNAME = os.environ["DSD_USERNAME"]
PASSWORD = os.environ["DSD_PASSWORD"]

# Authenticate Gmail
service = gmail_authenticate()

print("Downloading reports...")

# Each report has a unique ReportID
report_urls = {
    "Sales Summary": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972383",
    "Brand Performance": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972382",
    "Store-Level Trends": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972378",
    "Distribution Report": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972365",
}

report_paths = []

# Loop through each URL and download the report
for name, url in report_urls.items():
    print(f"Downloading {name}...")
    path = download_report(USERNAME, PASSWORD, url)
    print(f"Downloaded {name} to {path}")
    report_paths.append(path)

# Build the email body
email_body = """Hello,

Attached are today's four DSD reports:

1. Sales Summary  
2. Brand Performance  
3. Store-Level Trends  
4. Distribution Report  

Best regards,  
Bogmayer Automated System
"""

# Send one email with all 4 attachments
send_email_with_attachments(
    service=service,
    sender=os.environ["GMAIL_ADDRESS"],
    to="jackson@bogmayer.com",
    subject="Daily DSD Reports",
    attachment_paths=report_paths,
    body=email_body
)

print("Email sent with 4 DSD reports!")
