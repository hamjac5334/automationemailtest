#init everything
from dsd_downloader import download_report
from gmail_utils import gmail_authenticate, send_message_with_attachment
from datetime import datetime


USERNAME = "jackson@bogmayer.com"
PASSWORD = "Rosie121!121"
SENDER_EMAIL = "jackson@bogmayer.com"
RECEIVER_EMAIL = "jackson@bogmayer.com"

if __name__ == "__main__":
    print("Downloading report...")
    report_path = download_report(USERNAME, PASSWORD)
    print(f"Downloaded report to {report_path}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"Automated Report - {date_str}"

    print("Sending email...")
    service = gmail_authenticate()
    send_message_with_attachment(
        service,
        sender=SENDER_EMAIL,
        to=RECEIVER_EMAIL,
        subject=subject,
        body_text="Attached is the latest test automated report. This is currently run locally. I am setting up a server to run it globally",
        file=report_path,
    )
    print("Email sent!")
