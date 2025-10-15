import os
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def gmail_authenticate():
    token_data = os.environ["GMAIL_TOKEN"]
    creds = pickle.loads(base64.b64decode(token_data.encode()))

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    service = build("gmail", "v1", credentials=creds)
    return service

def send_email_with_attachments(service, sender, to, subject, attachment_paths=None):
    """
    Send an email with multiple attachments.
    attachment_paths should be a list of file paths.
    """
    message = MIMEMultipart()
    message["to"] = ", ".join(to) if isinstance(to, list) else str(to).strip()
    message["from"] = sender
    message["subject"] = subject
    message.attach(MIMEText(
        "Here are the automated reports attached from GitHub. "
        "This runs daily at 9am ET and includes multiple reports.", 
        "plain"
    ))

    if attachment_paths:
        for path in attachment_paths:
            with open(path, "rb") as f:
                part = MIMEBase("text", "csv")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(path)}")
            message.attach(part)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

