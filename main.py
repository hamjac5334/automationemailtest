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
    ("Store Counts 30 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23124246"),
    ("Store Counts 60 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23153930"),  
    ("Store Counts 90 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23157734")
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
    print("No reports downloaded. Exiting.")
    exit(1)

# Merge the three storecounts reports (5th, 6th, 7th)
merged_storecounts_df = storecounts.merge_three_storecounts_reports()

# Save the merged storecounts CSV
combined_storecounts_path = os.path.join(storecounts.DOWNLOAD_DIR, "combined_storecounts.csv")
merged_storecounts_df.to_csv(combined_storecounts_path, index=False)

# Provide the combined storecounts CSV path to csv_to_pdf for merging
set_storecounts_path(combined_storecounts_path)

pdf_files = []
# Convert reports 1-4 to PDF using merged storecounts inside
for csv_path in downloaded_files[:4]:
    try:
        pdf_path = csv_to_pdf(csv_path)
        pdf_files.append(pdf_path)
    except Exception as e:
        print(f"Failed to convert {csv_path} to PDF: {e}")

# Convert and add the combined storecounts report PDF for emailing
try:
    pdf_storecounts = csv_to_pdf(combined_storecounts_path)
    pdf_files.append(pdf_storecounts)
except Exception as e:
    print(f"Failed to convert combined storecounts CSV to PDF: {e}")

to_header = ", ".join(GMAIL_RECIPIENTS)

subject = "Automated DSD Reports"
body = """This is an automated email test.

Attached are the latest DSD reports as PDFs. 
These are live inventory snapshots of:
1. SCP/KW in SC
2. SCP in GA
3. Tryon
4. Cavalier
5. Store Counts Summary (30, 60, and 90 days combined)
"""

try:
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=to_header,
        subject=subject,
        body=body,
        attachments=pdf_files
    )
    print("\nEmail sent successfully.")
except Exception as e:
    print(f"\nFailed to send email: {e}")
