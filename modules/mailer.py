import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from models import db, Email, SendLog
from config import Config

def get_today_send_count():
    """
    Returns the number of emails sent today according to the log.
    Filtered for status='sent'.
    """
    today = date.today()
    return SendLog.query.filter(
        db.func.date(SendLog.sent_at) == today,
        SendLog.status == 'sent'
    ).count()

def send_outreach_email(email_id, app, dry_run=False):
    """
    Sends a specific email record via Gmail SMTP.
    Enforces daily rate limits and logs the result.
    """
    with app.app_context():
        email_record = Email.query.get(email_id)
        if not email_record:
            return "Email not found", False

        # 1. Check Rate Limit
        current_count = get_today_send_count()
        if current_count >= Config.DAILY_EMAIL_LIMIT:
            log_entry = SendLog(
                email_id=email_id,
                status='skipped',
                error_msg=f"Daily limit of {Config.DAILY_EMAIL_LIMIT} reached."
            )
            db.session.add(log_entry)
            db.session.commit()
            return "Daily limit reached", False

        # 2. Logic for Dry-Run
        if dry_run:
            log_entry = SendLog(
                email_id=email_id,
                status='skipped',
                error_msg="Dry-run mode enabled. Email not sent."
            )
            db.session.add(log_entry)
            email_record.status = 'sent' # Mark as sent for UI consistency in dry-run if desired
            db.session.commit()
            return "Dry run: Logged", True

        # 3. SMTP Send
        try:
            # Dynamically reload env vars so user doesn't have to restart the server
            from dotenv import load_dotenv
            import os
            load_dotenv(override=True)
            live_user = os.getenv('GMAIL_USER', Config.GMAIL_USER)
            live_pass = os.getenv('GMAIL_APP_PASSWORD', Config.GMAIL_APP_PASSWORD)

            msg = MIMEMultipart()
            msg['From'] = live_user
            msg['To'] = email_record.email
            msg['Subject'] = email_record.subject
            msg.attach(MIMEText(email_record.email_body, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(live_user, live_pass)
            server.send_message(msg)
            server.quit()

            # Record Success
            log_entry = SendLog(email_id=email_id, status='sent')
            db.session.add(log_entry)
            email_record.status = 'sent'
            db.session.commit()
            return "Success", True

        except Exception as e:
            error_details = str(e)
            print(f">>> [SMTP ERROR] Failed to send email ID {email_id}: {error_details}")
            # Record Failure
            log_entry = SendLog(
                email_id=email_id, 
                status='failed', 
                error_msg=error_details
            )
            db.session.add(log_entry)
            email_record.status = 'failed'
            db.session.commit()
            return error_details, False

def send_all_approved(app, dry_run=False):
    """
    Iterates through all approved emails and attempts to send them.
    Returns count of successful sends.
    """
    with app.app_context():
        # Fetch all emails that are approved or drafts ready for sending
        emails_to_send = Email.query.filter(
            Email.status.in_(['approved', 'draft']),
            Email.email != "",
            Email.subject != None
        ).all()
        
        success_count = 0
        for e in emails_to_send:
            _, success = send_outreach_email(e.id, app, dry_run=dry_run)
            if success:
                success_count += 1
            # If we hit the limit, stop early
            if get_today_send_count() >= Config.DAILY_EMAIL_LIMIT:
                break
                
        return success_count
