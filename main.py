#init everything
from dsd_downloader import download_report
from gmail_utils import gmail_authenticate, send_email_with_attachments
import os

USERNAME = os.environ["DSD_USERNAME"]
PASSWORD = os.environ["DSD_PASSWORD"]

print("Downloading report...")
report_paths = []

# Download 4 reports
for i in range(4):
    print(f"Downloading report {i + 1}...")
    path = download_report(USERNAME, PASSWORD, report_number=i+1)
    print(f"Downloaded report {i + 1} to {path}")
    report_paths.append(path)

# Authenticate Gmail
service = gmail_authenticate()

#mason.holland@hollandplace.net, chad.elkins@tapsandtables.net
recipients = os.environ.get("GMAIL_RECIPIENT", "jackson@bogmayer.com")

send_email_with_attachments(
    service=service,
    sender=os.environ["GMAIL_ADDRESS"],
    to=recipients,
    subject="Daily Automated Reports",
    attachment_paths=report_paths
)

print("Email sent with 4 reports!")
