#init everything
import os
import sys
from dsd_downloader import download_report
from send_email import send_email_with_attachments

print("Downloading reports...")

USERNAME = os.getenv("DSD_USERNAME")
PASSWORD = os.getenv("DSD_PASSWORD")
EMAIL_SENDER = os.getenv("GMAIL_ADDRESS")
EMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")
EMAIL_TOKEN = os.getenv("GMAIL_TOKEN")

# ✅ Add all your report URLs here (customize as needed)
REPORTS = {
    "Sales Summary": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972383",
    "Brand Performance": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972384",
    "Weekly Volume": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972385",
    "Retail Sales": "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972386"
}

# ✅ Directory to save all reports
OUTPUT_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")
os.makedirs(OUTPUT_DIR, exist_ok=True)

downloaded_files = []

for name, url in REPORTS.items():
    print(f"\nDownloading {name}...")
    try:
        file_path = download_report(USERNAME, PASSWORD, url)
        downloaded_files.append(file_path)
    except Exception as e:
        print(f"⚠️ Failed to download {name}: {e}")
        continue

# ✅ Verify at least one file downloaded
if not downloaded_files:
    print("❌ No reports downloaded. Exiting.")
    sys.exit(1)

print("\n✅ All available reports downloaded:")
for f in downloaded_files:
    print(f" - {f}")

# ✅ Send the email with all downloaded reports attached
try:
    print("\nSending email with attachments...")
    send_email_with_attachments(
        sender=EMAIL_SENDER,
        recipient=EMAIL_RECIPIENT,
        token=EMAIL_TOKEN,
        subject="Automated DSD Reports",
        body="Attached are the latest DSD reports from the automated system.",
        attachments=downloaded_files
    )
    print("✅ Email sent successfully.")
except Exception as e:
    print(f"❌ Failed to send email: {e}")
    sys.exit(1)

print("\n🎉 Workflow completed successfully.")
