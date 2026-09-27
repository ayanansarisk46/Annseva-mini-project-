"""
================================================================================
AnnSeva - Email Notification Service (services/email_service.py)
================================================================================
College Viva Note:
This module demonstrates modular notification architecture.
In production, it connects to an SMTP server (e.g. Gmail/SendGrid) to send emails.
In development or viva demo, if credentials are empty, it gracefully logs the 
notification to the console without breaking execution.
Security: Passwords and usernames are loaded strictly from environment variables.
================================================================================
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def send_email_notification(recipient_email, subject, body_text):
    """
    Sends an email notification to donor or NGO.
    Falls back to console logger if SMTP is not configured.
    """
    if not recipient_email:
        return False

    # Check if SMTP credentials are provided
    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        print("\n--- [EMAIL NOTIFICATION MOCK DISPATCH] ---")
        print(f"To:      {recipient_email}")
        print(f"Subject: {subject}")
        print(f"Body:    {body_text}")
        print("------------------------------------------\n")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = Config.MAIL_DEFAULT_SENDER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain'))

        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
        if Config.MAIL_USE_TLS:
            server.starttls()
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        server.sendmail(Config.MAIL_DEFAULT_SENDER, recipient_email, msg.as_string())
        server.quit()
        print(f"[EMAIL] Successfully sent email to {recipient_email}")
        return True
    except Exception as e:
        print(f"[EMAIL WARNING] Failed to send email to {recipient_email}: {e}")
        return False
