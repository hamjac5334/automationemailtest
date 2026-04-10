import os
from dsd_downloader import start_driver, login, download_report
from gmail_utils import send_email_with_attachments
from run_auto_eda import run_eda_and_download_report
from datetime import datetime
import shutil
import storecounts
from csv_to_pdf import csv_to_pdf, set_storecounts_path, set_eda_config, split_and_convert_by_location

USERNAME = os.environ.get("DSD_USERNAME")
PASSWORD = os.environ.get("DSD_PASSWORD")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
#, "mason.holland@hollandplace.net", "chad.elkins@tapsandtables.net", "michael.gallo@islandbrandsusa.com", "jared@bogmayer.com"
#additional members: ,"carter@islandbrandsusa.com", "lauryn@rustybullbrewing.com", "max@southernbarrel.com", "ben@rustybullbrewing.com"
#GMAIL_RECIPIENTS = ["jackson@bogmayer.com" , "mason.holland@hollandplace.net", "chad.elkins@tapsandtables.net", "michael.gallo@islandbrandsusa.com", "jared@bogmayer.com", "ben@rustybullbrewing.com"]
#GMAIL_RECIPIENTS = ["jackson@bogmayer.com"]

MAIN_RECIPIENTS = [
    "jackson@bogmayer.com",
    "mason.holland@hollandplace.net",
    "chad.elkins@tapsandtables.net",
    "jared@bogmayer.com",
    "ben@rustybullbrewing.com" 
]

CHARLESTON_RECIPIENTS = [
    "jackson@bogmayer.com", 
    "michael.gallo@islandbrandsusa.com",
    "carter@islandbrandsusa.com",
    "lauryn@rustybullbrewing.com", 
    "max@southernbarrel.com", 
    "ben@rustybullbrewing.com"
    
]

GEORGIA_RECIPIENTS = [
    "jackson@bogmayer.com", 
    "michael.gallo@islandbrandsusa.com",
    "max@southernbarrel.com", 
    "ben@rustybullbrewing.com"
]

CONSOLIDATED_RECIPIENTS = [
    "jackson@bogmayer.com",
    "michael.gallo@islandbrandsusa.com",
    "mason.holland@hollandplace.net"
    
]


REPORTS = [
    #First report group
    ("SC_SCP", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972383"),
    ("Georgia_SCP", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972382"),
    ("Tryon", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972378"),
    ("Cavalier", "https://dsdlink.com/Home?DashboardID=100120&ReportID=22972365"),
    ("Store Counts 30 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23124246"),
    ("Store Counts 60 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23153930"),  
    ("Store Counts 90 Days", "https://dsdlink.com/Home?DashboardID=100120&ReportID=23157734"),

    #second report group
    #("Rusty Bull", "https://dsdlink.com/Home?DashboardID=100120&ReportID=24153712"), 
    #("Southern Barrel", "https://dsdlink.com/Home?DashboardID=100120&ReportID=24153732"),

    #Third report group:
    ("Rusty Bull", "https://dsdlink.com/Home?DashboardID=100120&ReportID=24153712"), 
    ("Southern Barrel", "https://dsdlink.com/Home?DashboardID=100120&ReportID=24153732"),
    ("Georgia_All_SCP", "https://dsdlink.com/Home?DashboardID=100120&ReportID=24478351"),

    #fourth report group
    #South Carolina Consolidated Inventory
    ("Consolidated", "https://dsdlink.com/Home?DashboardID=100120&ReportID=24721804")
    
]

print("Downloading reports...\n")

driver, wait = start_driver()
login(driver, wait, USERNAME, PASSWORD)

downloaded_files = []
for i, (report_name, url) in enumerate(REPORTS, start=1):
    try:
        print(f"Downloading {report_name}...")
        path = download_report(driver, wait, url, report_name)
        downloaded_files.append(path)
    except Exception as e:
        print(f"Failed to download {report_name}: {e}")

driver.quit()

print("\nAll CSVs after download:")
for f in downloaded_files:
    print(f"  {f} (exists: {os.path.isfile(f) if f else 'N/A'})")

if len(downloaded_files) < len(REPORTS):
    print("Warning: Not all reports downloaded successfully.")

storecount_files = [
    f for f in downloaded_files
    if f and "store_counts" in f
]

# Merge storecounts if all 3 files are present
combined_storecounts_path = None
if len(storecount_files) == 3:
    merged_storecounts_df = storecounts.merge_three_storecounts_reports()
    combined_storecounts_path = os.path.join(storecounts.DOWNLOAD_DIR, "combined_storecounts.csv")
    merged_storecounts_df.to_csv(combined_storecounts_path, index=False)
    set_storecounts_path(combined_storecounts_path)
    print(f"✓ Merged storecounts saved to: {combined_storecounts_path}")
else:
    print("Warning: Missing one or more storecounts files; skipping merge.")

# Configure EDA settings
dashboard_url = "https://automatedanalytics.onrender.com/"
set_eda_config(storecounts.DOWNLOAD_DIR, dashboard_url)

storecounts_30_csv = next((f for f in downloaded_files if "30_days" in f), None)
storecounts_60_csv = next((f for f in downloaded_files if "60_days" in f), None)
storecounts_90_csv = next((f for f in downloaded_files if "90_days" in f), None)

# Convert CSVs to PDF (EDA will run automatically on the first one)
print("\nConverting CSVs to PDFs...")
pdf_files = []

# Convert main reports to PDF - EDA runs on the FIRST report
for idx, csv_path in enumerate(downloaded_files): 
    if csv_path and os.path.isfile(csv_path):
        try:
            # Run EDA only on the first report (idx == 0)
            pdf_path = csv_to_pdf(csv_path, run_eda_on_first=(idx == 0))
            print(f"Converted {csv_path} -> {pdf_path}, exists: {os.path.isfile(pdf_path) if pdf_path else 'N/A'}")
            if pdf_path and os.path.isfile(pdf_path):
                pdf_files.append(pdf_path)
            else:
                print(f"[WARN] PDF for {csv_path} missing after conversion!")
        except Exception as e:
            print(f"Failed to convert {csv_path} to PDF: {e}")

# Convert storecounts CSVs to PDF (if present)
for sc_csv in (storecounts_30_csv, storecounts_60_csv, storecounts_90_csv):
    if sc_csv and os.path.isfile(sc_csv):
        try:
            sc_pdf = csv_to_pdf(sc_csv)
            print(f"Converted {sc_csv} -> {sc_pdf}, exists: {os.path.isfile(sc_pdf) if sc_pdf else 'N/A'}")
            if sc_pdf and os.path.isfile(sc_pdf):
                pdf_files.append(sc_pdf)
            else:
                print(f"[WARN] Storecounts PDF for {sc_csv} missing after conversion!")
        except Exception as e:
            print(f"Failed to convert storecounts CSV {sc_csv} to PDF: {e}")

# Check for EDA PDF and add it to the list
today = datetime.now().strftime("%Y-%m-%d")
eda_pdf_path = os.path.join(storecounts.DOWNLOAD_DIR, f"Report_{today}_EDA.pdf")
if os.path.isfile(eda_pdf_path):
    pdf_files.append(eda_pdf_path)
    print(f"✓ Appended EDA PDF: {eda_pdf_path}")

# Debug output
print("\n=== DEBUGGING PDF FILES ===")
print(f"Download directory: {storecounts.DOWNLOAD_DIR}")
print(f"Directory contents: {os.listdir(storecounts.DOWNLOAD_DIR)}")
print("\nPDF files list:")
for f in pdf_files:
    abs_path = os.path.abspath(f)
    print(f"  {f}")
    print(f"    Absolute: {abs_path}")
    print(f"    Exists: {os.path.isfile(f)}")
    if os.path.isfile(f):
        print(f"    Size: {os.path.getsize(f)} bytes")
print("=== END DEBUG ===\n")

print("\nFinal list of PDFs to attach:")
for f in pdf_files:
    print(f"  {f} (exists: {os.path.isfile(f)})")

valid_attachments = [f for f in pdf_files if os.path.isfile(f)]
print(f"\n Found {len(valid_attachments)} valid PDF attachments")

if not valid_attachments:
    print("\n[ERROR] No valid PDF attachments found! Email will be sent without attachments.")
else:
    print("\nSending email with these attachments:")
    for f in valid_attachments:
        print(f"  {f}")

print("\nGrouping PDFs for email distribution...")

all_pdfs = [f for f in pdf_files if os.path.isfile(f)]

# Main gets everything
main_pdfs = all_pdfs.copy()

#Indexing for bottom groups
CHARLESTON_INDEXES = [0,7, 8] 
GEORGIA_INDEXES = [7,8,9] 


charleston_pdfs = [
    all_pdfs[i] for i in CHARLESTON_INDEXES
    if i < len(all_pdfs)
]

georgia_pdfs = [
    all_pdfs[i] for i in GEORGIA_INDEXES
    if i < len(all_pdfs)
]

print(f"Main PDFs: {len(main_pdfs)}")
print(f"Charleston PDFs: {len(charleston_pdfs)}")
print(f"Georgia PDFs: {len(georgia_pdfs)}")

send_email_with_attachments(
    sender=GMAIL_ADDRESS,
    to=", ".join(MAIN_RECIPIENTS),
    subject="Automated DSD Reports - Full",
    body="Full report set attached.",
    attachments=main_pdfs
)
print("Sent MAIN email")

if charleston_pdfs:
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=", ".join(CHARLESTON_RECIPIENTS),
        subject="Charleston Island Reports",
        body="South Carolina SCP reports attached.",
        attachments= charleston_pdfs
    )
    print("Sent Charleston email")
else:
    print("No Charleston PDFs found")

if georgia_pdfs:
    send_email_with_attachments(
        sender=GMAIL_ADDRESS,
        to=", ".join(GEORGIA_RECIPIENTS),
        subject="Georgia Reports",
        body="Georgia-specific reports attached.",
        attachments=georgia_pdfs
    )
    print("Sent Georgia email")
else:
    print("No Georgia PDFs found")

# --- 4th group: Consolidated report split by Location ---
consolidated_csv = next(
    (f for f in downloaded_files if f and "consolidated" in f.lower()),
    None
)

if consolidated_csv and os.path.isfile(consolidated_csv):
    print("\nSplitting Consolidated report by Location...")
    try:
        consolidated_pdfs = split_and_convert_by_location(consolidated_csv)
        if consolidated_pdfs:
            send_email_with_attachments(
                sender=GMAIL_ADDRESS,
                to=", ".join(CONSOLIDATED_RECIPIENTS),
                subject="Consolidated Inventory Reports by Location",
                body="Consolidated inventory split by location — one PDF per location attached.",
                attachments=consolidated_pdfs
            )
            print(f"Sent Consolidated email ({len(consolidated_pdfs)} PDFs)")
        else:
            print("No Consolidated PDFs generated; skipping email.")
    except Exception as e:
        print(f"Failed to process Consolidated report: {e}")
else:
    print("Consolidated CSV not found; skipping 4th group email.")
