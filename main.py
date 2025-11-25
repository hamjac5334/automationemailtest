import os
from dsd_downloader import download_report
from gmail_utils import send_email_with_attachments
from csv_to_pdf import csv_to_pdf, set_storecounts_path
from run_auto_eda import run_eda_and_download_report
from datetime import datetime
import shutil
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
        print(f"❌ Failed to download {report_name}: {e}")
        downloaded_files.append(None)

print("\nAll CSVs after download:")
for f in downloaded_files:
    print(f"  {f}  (exists: {os.path.isfile(f) if f else 'N/A'})")

if len(downloaded_files) < len(REPORTS):
    print("⚠️ Warning: Not all reports downloaded.")


# ----------------------------------------------------------------------
# 2. DETECT STORECOUNTS (5, 6, 7)
# ----------------------------------------------------------------------
expected_storecounts = ["_5.csv", "_6.csv", "_7.csv"]

storecount_files = [
    f for f in downloaded_files
    if f and any(f.endswith(s) for s in expected_storecounts)
]

storecounts_30_csv = next((f for f in storecount_files if f.endswith("_5.csv")), None)
storecounts_60_csv = next((f for f in storecount_files if f.endswith("_6.csv")), None)
storecounts_90_csv = next((f for f in storecount_files if f.endswith("_7.csv")), None)

print("\nDetected Storecount Files:")
print(f"  30-day: {storecounts_30_csv}")
print(f"  60-day: {storecounts_60_csv}")
print(f"  90-day: {storecounts_90_csv}")


# ----------------------------------------------------------------------
# 3. MERGE STORECOUNTS IF WE HAVE ALL 3
# ----------------------------------------------------------------------
if len(storecount_files) == 3:
    print("\nMerging storecounts...")
    merged_df = storecounts.merge_three_storecounts_reports()
    combined_storecounts_path = os.path.join(storecounts.DOWNLOAD_DIR, "combined_storecounts.csv")
    merged_df.to_csv(combined_storecounts_path, index=False)

    set_storecounts_path(combined_storecounts_path)
    print(f"Combined storecounts written to: {combined_storecounts_path}")
else:
    print("⚠️ Missing storecounts files — skipping merge.")


# ----------------------------------------------------------------------
# 4. CONVERT ALL MAIN REPORT CSVs TO PDF
# ----------------------------------------------------------------------
pdf_files = []

print("\nConverting CSVs to PDFs...")

for csv_path in downloaded_files:
    if csv_path and os.path.isfile(csv_path):

        try:
            pdf = csv_to_pdf(csv_path)
            if pdf and os.path.isfile(pdf):
                pdf_files.append(pdf)
                print(f"  ✅ {csv_path} → {pdf}")
            else:
                print(f"  ⚠️ Missing PDF output for {csv_path}")

        except Exception as e:
            print(f"❌ Failed converting {csv_path}: {e}")

    else:
        print(f"  ⚠️ Skipping missing CSV: {csv_path}")


# ----------------------------------------------------------------------
# 5. RUN EDA ON THE SECOND REPORT (IF VALID)
# ----------------------------------------------------------------------
dashboard_url = "https://automatedanalytics.onrender.com/"

target_for_eda = (
    downloaded_files[1]
    if len(downloaded_files) > 1 and downloaded_files[1] and os.path.isfile(downloaded_files[1])
    else None
)

if target_for_eda:
    print(f"\nRunning EDA on: {target_for_eda}")

    try:
        eda_pdf_path = run_eda_and_download_report(target_for_eda, dashboard_url, storecounts.DOWNLOAD_DIR)

        if eda_pdf_path and os.path.isfile(eda_pdf_path):

            today = datetime.now().strftime("%Y-%m-%d")
            final_eda_pdf = os.path.join(storecounts.DOWNLOAD_DIR, f"Report_{today}_EDA.pdf")

            shutil.move(eda_pdf_path, final_eda_pdf)
            pdf_files.append(final_eda_pdf)

            print(f"  ✅ EDA PDF saved: {final_eda_pdf}")

        else:
            print("⚠️ EDA PDF missing!")

    except Exception as e:
        print(f"❌ Failed to run EDA: {e}")
else:
    print("⚠️ No valid CSV for EDA — skipping EDA step.")


# ----------------------------------------------------------------------
# 6. FINAL ATTACHMENTS LIST
# ----------------------------------------------------------------------
valid_attachments = [p for p in pdf_files if os.path.isfile(p)]

print("\nFinal PDFs:")
for f in valid_attachments:
    print(f"  {f}")


# ----------------------------------------------------------------------
# 7. SEND EMAIL
# ----------------------------------------------------------------------
try:
    print("\nSending email...")
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=", ".join(GMAIL_RECIPIENTS),
        subject="Automated DSD Reports",
        body=(
            "This is an automated email.\n\n"
            "Attached are the latest DSD reports as PDFs:\n"
            "1. SCP/KW in SC\n"
            "2. SCP in GA\n"
            "3. Tryon\n"
            "4. Cavalier\n"
            "5. List of Retail Stores\n"
        ),
        attachments=valid_attachments
    )
    print("\n📨 Email sent successfully.")

except Exception as e:
    print(f"\n❌ Failed to send email: {e}")
