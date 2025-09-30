#init everything
from dsd_downloader import download_report
# from gmail_utils import gmail_authenticate, send_message

import os

USERNAME = os.environ["DSD_USERNAME"]
PASSWORD = os.environ["DSD_PASSWORD"]

print("Downloading report...")
report_path = download_report(USERNAME, PASSWORD)
print(f"Downloaded report to {report_path}")

# ---- TEMP DISABLED GMAIL ----
# print("Sending email...")
# service = gmail_authenticate()
# send_message(service, "your_email@example.com", "Report", "Here is the report.", report_path)
# print("Email sent!")
