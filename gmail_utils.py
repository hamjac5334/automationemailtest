import os
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def gmail_authenticate():
    token_data = os.environ["GMAIL_TOKEN"]
    creds = pickle.loads(base64.b64decode(token_data.encode()))

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    service = build("gmail", "v1", credentials=creds)
    return service

def send_email_with_attachments(sender, to, subject, body, attachments):
    """
    Send an email with multiple attachments using Gmail API using the GMAIL_TOKEN env variable.
    """
    # Load credentials from env variable
    token_data = os.environ["GMAIL_TOKEN"]
    creds = pickle.loads(base64.b64decode(token_data.encode()))

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

    service = build('gmail', 'v1', credentials=creds)

    # Create the email
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = to
    message['Subject'] = subject

    # Add body
    message.attach(MIMEText(body, 'plain'))

    # Attach files
    for file_path in attachments:
        part = MIMEBase('application', 'octet-stream')
        with open(file_path, 'rb') as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{os.path.basename(file_path)}"'
        )
        message.attach(part)

    # Encode and send
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
