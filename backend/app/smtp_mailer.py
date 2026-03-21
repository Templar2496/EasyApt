import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .email_templates import (
    get_appointment_confirmation_email,
    get_appointment_cancellation_email,
    get_appointment_reminder_email,
    get_appointment_rescheduled_email,
    get_account_created_email,
)


def send_smtp_email(to_email, subject, html_content):
    """Send email via SMTP (Gmail/Yahoo)"""
    
    # === CHANGED: Use settings instead of os.getenv ===
    from .config import settings
    
    # DEMO MODE: simulate email sending (no SMTP)
    if settings.MAILTRAP_MODE.lower() == "true":
        print("[DEMO MODE] Email simulated")
        print("To:", to_email)
        print("Subject:", subject)
        return True
    
    # === CHANGED: Use settings for all SMTP config ===
    host = settings.MAILTRAP_HOST or 'sandbox.smtp.mailtrap.io'
    port = int(settings.MAILTRAP_PORT) if settings.MAILTRAP_PORT else 2525
    username = settings.MAILTRAP_USERNAME
    password = settings.MAILTRAP_PASSWORD
    from_email = settings.SENDGRID_FROM_EMAIL
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    try:
        server = smtplib.SMTP(host, port)
        server.starttls()  # Enable TLS encryption
        server.login(username, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        return False


def send_confirmation_email(to_email, patient_name, appointment_date, appointment_time, provider_name, cancel_url=None, reschedule_url=None):
    html = get_appointment_confirmation_email(patient_name, appointment_date, appointment_time, provider_name, cancel_url=cancel_url, reschedule_url=reschedule_url)
    subject = f"✅ Appointment Confirmed - {appointment_date}"
    return send_smtp_email(to_email, subject, html)


def send_cancellation_email(to_email, patient_name, appointment_date, appointment_time, provider_name):
    html = get_appointment_cancellation_email(patient_name, appointment_date, appointment_time, provider_name)
    subject = f"❌ Appointment Cancelled - {appointment_date}"
    return send_smtp_email(to_email, subject, html)


def send_reminder_email(to_email, patient_name, appointment_date, appointment_time, provider_name):
    html = get_appointment_reminder_email(patient_name, appointment_date, appointment_time, provider_name)
    subject = f"⏰ Appointment Reminder - {appointment_date}"
    return send_smtp_email(to_email, subject, html)


def send_rescheduled_email(
    to_email,
    patient_name,
    old_date,
    old_time,
    new_date,
    new_time,
    provider_name
):
    html = get_appointment_rescheduled_email(
        patient_name,
        old_date,
        old_time,
        new_date,
        new_time,
        provider_name
    )
    subject = f"📅 Appointment Rescheduled - {new_date}"
    return send_smtp_email(to_email, subject, html)


def send_account_created_email(to_email, name):
    html = get_account_created_email(name)
    subject = "🎉 Welcome to EasyAPT!"
    return send_smtp_email(to_email, subject, html)
