import os
from dsd_downloader import download_report
from gmail_utils import send_email_with_attachments
from csv_to_pdf import csv_to_pdf, set_storecounts_path
import storecounts

USERNAME = os.environ.get("DSD_USERNAME")
PASSWORD = os.environ.get("DSD_PASSWORD")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
#,"mason.holland@hollandplace.net", "chad.elkins@tapsandtables.net"
GMAIL_RECIPIENTS = ["jackson@bogmayer.com"]

REPORTS = [
    ("Sales Summary", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972383"),
    ("Brand Performance", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972382"),
    ("Weekly Volume", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972378"),
    ("Retail Sales", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972365"),
    ("values", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23124246")
]

print("Downloading reports...\n")
downloaded_files = []
for i, (report_name, url) in enumerate(REPORTS, start=1):
    try:
        print(f"Downloading {report_name}...")
        path = download_report(USERNAME, PASSWORD, url, report_number=i)
        downloaded_files.append(path)
    except Exception as e:
        print(f" Failed to download {report_name}: {e}")

if not downloaded_files:
    print(" No reports downloaded. Exiting.")
    exit(1)

# Generate storecounts from last report (report 5)
last_csv = storecounts.load_last_report()
storecounts_df = storecounts.add_store_value_counts(last_csv)
storecounts_path = last_csv.replace(".csv", "_with_storecounts.csv")
storecounts_df.to_csv(storecounts_path, index=False)

# Tell csv_to_pdf where the storecounts file is
set_storecounts_path(storecounts_path)


#Pdf conversion
pdf_files = []
for csv_path in downloaded_files[:-1]:  # reports 1-4, excluding last
    try:
        pdf_path = csv_to_pdf(csv_path)
        pdf_files.append(pdf_path)
    except Exception as e:
        print(f"Failed to convert {csv_path} to PDF: {e}")

# Convert and append the storecounts report PDF for emailing
try:
    pdf_storecounts = csv_to_pdf(storecounts_path)
    pdf_files.append(pdf_storecounts)
except Exception as e:
    print(f"Failed to convert storecounts CSV to PDF: {e}")

to_header = ", ".join(GMAIL_RECIPIENTS)

subject = "Automated DSD Reports"
body = """This is an automated email test.

Attached are the latest DSD reports as PDFs. 
These are live inventory snapshots of:
1. SCP/KW in SC
2. SCP in GA
3. Tryon
4. Cavalier
5. Store Counts Summary
"""

try:
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=to_header,
        subject=subject,
        body=body,
        attachments=pdf_files  # PDFs including the storecounts report now
    )
    print("\nEmail sent successfully.")
except Exception as e:
    print(f"\nFailed to send email: {e}")

