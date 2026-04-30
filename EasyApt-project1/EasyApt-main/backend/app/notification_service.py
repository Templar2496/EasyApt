"""
Notification Service for EasyAPT
Handles SMS and Email notifications for appointments
Author: Emil K
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from datetime import datetime
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications"""
    BOOKING_CONFIRMATION = "booking_confirmation"
    APPOINTMENT_REMINDER = "appointment_reminder"
    CANCELLATION = "cancellation"
    RESCHEDULING = "rescheduling"


class NotificationService:
    """
    Handles all notification operations for the appointment system.
    Supports both SMS (Twilio) and Email (SMTP via Mailtrap/Gmail) notifications.
    """

    def __init__(self):
        # === CHANGED: Use settings instead of os.getenv ===
        from .config import settings
        
        # Twilio configuration
        self.twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        self.twilio_phone_number = settings.TWILIO_PHONE_NUMBER

        # SendGrid configuration (kept for compatibility)
        self.sendgrid_api_key = settings.SENDGRID_API_KEY
        self.sendgrid_from_email = settings.SENDGRID_FROM_EMAIL

        # Initialize clients
        self.twilio_client = None
        self.sendgrid_client = None

        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        else:
            logger.warning("Twilio credentials not found. SMS notifications disabled.")

        if self.sendgrid_api_key:
            self.sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
        else:
            logger.warning("SendGrid API key not found. Email notifications disabled.")

        # Initialize scheduler
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        }
        self.scheduler = AsyncIOScheduler(jobstores=jobstores)
        self.scheduler.start()

    async def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS notification via Twilio or TEST MODE"""

        # === CHANGED: Use settings instead of os.getenv ===
        from .config import settings
        
        # Test Mode enabled?
        if settings.TWILIO_TEST_MODE.lower() == "true":
            logger.info(f"[TEST MODE SMS] To: {to_phone} | Message: {message}")
            return True

        if not self.twilio_client:
            logger.error("Twilio client not initialized")
            return False

        try:
            message_response = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=to_phone
            )
            logger.info(f"SMS sent successfully. SID: {message_response.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False

    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
            """Send email notification via Mailtrap SMTP"""

            # Use SMTP instead of SendGrid
            from .smtp_mailer import send_smtp_email

            try:
                success = send_smtp_email(to_email, subject, html_content)
                if success:
                    logger.info(f"Email sent successfully to {to_email}")
                else:
                    logger.error(f"Failed to send email to {to_email}")
                return success
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}")
                return False

    async def send_booking_confirmation(
        self,
        patient_phone: str,
        patient_email: str,
        patient_name: str,
        appointment_date: datetime,
        provider_name: str
    ) -> dict:
        """Send booking confirmation via SMS and Email"""
        date_str = appointment_date.strftime("%B %d, %Y at %I:%M %p")
        masked_provider = provider_name.split()[0][0] + "***" if provider_name else "your provider"

        sms_message = (
            f"EasyAPT: Your appointment is confirmed for {date_str}. "
            f"Reply STOP to unsubscribe."
        )

        email_subject = "Appointment Confirmation - EasyAPT"
        email_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Appointment Confirmed</h2>
                <p>Dear {patient_name},</p>
                <p>Your appointment has been successfully scheduled:</p>
                <ul>
                    <li><strong>Date &amp; Time:</strong> {date_str}</li>
                    <li><strong>Provider:</strong> {provider_name}</li>
                </ul>
                <p>You will receive a reminder 24 hours before your appointment.</p>
                <br>
                <p>Best regards,<br>EasyAPT Team</p>
            </body>
        </html>
        """

        sms_sent = await self.send_sms(patient_phone, sms_message)
        email_sent = await self.send_email(patient_email, email_subject, email_html)

        reminder_time = appointment_date - timedelta(hours=24)
        reminder_scheduled_flag = reminder_time > datetime.now()

        if reminder_scheduled_flag:
            self.schedule_reminder(
                patient_phone, patient_email, patient_name,
                appointment_date, masked_provider, reminder_time
            )

        return {
            "sms_sent": sms_sent,
            "email_sent": email_sent,
            "reminder_scheduled": reminder_scheduled_flag
        }

    def schedule_reminder(self, patient_phone, patient_email, patient_name, appointment_date, provider_name, reminder_time):
        """Schedule a reminder notification. Returns job_id (str) or None."""
        job_id = f"reminder_{appointment_date.isoformat()}_{patient_email}"
        try:
            self.scheduler.add_job(
                self.send_appointment_reminder,
                'date',
                run_date=reminder_time,
                args=[patient_phone, patient_email, patient_name, appointment_date, provider_name],
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Reminder scheduled for {reminder_time} | job_id={job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {str(e)}")
            return None

    def cancel_reminder(self, job_id: str) -> bool:
        """Cancel an existing scheduled reminder job by job_id."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled reminder job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not cancel reminder job (maybe not found): {job_id} | {e}")
            return False

    async def send_appointment_reminder(
        self,
        patient_phone,
        patient_email,
        patient_name,
        appointment_date,
        provider_name
    ):

        """Send appointment reminder via SMS and Email"""

        date_str = appointment_date.strftime("%B %d, %Y at %I:%M %p")
        provider_display = provider_name if provider_name else "your provider"

        # --- SMS Logic ---
        sms_message = (
            f"EasyAPT Reminder: You have an appointment on {date_str} "
            f"with {provider_display}. Reply STOP to unsubscribe."
        )
        sms_sent = False
        if patient_phone:
            sms_sent = await self.send_sms(patient_phone, sms_message)

        # --- Email Logic ---
        email_subject = "Appointment Reminder - EasyAPT"
        email_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Appointment Reminder</h2>
                <p>Dear {patient_name},</p>
                <p>This is a reminder of your upcoming appointment:</p>
                <ul>
                    <li><strong>Date &amp; Time:</strong> {date_str}</li>
                    <li><strong>Provider:</strong> {provider_display}</li>
                </ul>
                <p>If you need to cancel or reschedule, please contact the office.</p>
                <br>
                <p>Best regards,<br>EasyAPT Team</p>
            </body>
        </html>
        """
        email_sent = False
        if patient_email:
            email_sent = await self.send_email(patient_email, email_subject, email_html)

        logger.info(
            f"Reminder sent. SMS={sms_sent}, Email={email_sent}, "
            f"User={patient_name}, Time={date_str}"
        )

        return { "sms_sent": sms_sent, "email_sent": email_sent }

    def shutdown(self):
        """Gracefully shutdown the scheduler"""
        self.scheduler.shutdown()

    async def send_cancellation_email(
        self,
        patient_email: str,
        patient_name: str,
        appointment_date: datetime,
        provider_name: str
    ) -> bool:
        """Send appointment cancellation email"""
        from .smtp_mailer import send_cancellation_email
        
        try:
            date_str = appointment_date.strftime("%B %d, %Y")
            time_str = appointment_date.strftime("%I:%M %p")
            
            success = send_cancellation_email(
                to_email=patient_email,
                patient_name=patient_name,
                appointment_date=date_str,
                appointment_time=time_str,
                provider_name=provider_name
            )
            
            if success:
                logger.info(f" Cancellation email sent to {patient_email}")
            else:
                logger.error(f" Failed to send cancellation email to {patient_email}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending cancellation email: {str(e)}")
            return False

    async def send_reschedule_email(
        self,
        patient_email: str,
        patient_name: str,
        old_date: datetime,
        new_date: datetime,
        provider_name: str
    ) -> bool:
        """Send appointment reschedule email"""
        from .smtp_mailer import send_rescheduled_email
        
        try:
            old_date_str = old_date.strftime("%B %d, %Y")
            old_time_str = old_date.strftime("%I:%M %p")
            new_date_str = new_date.strftime("%B %d, %Y")
            new_time_str = new_date.strftime("%I:%M %p")
            
            success = send_rescheduled_email(
                to_email=patient_email,
                patient_name=patient_name,
                old_date=old_date_str,
                old_time=old_time_str,
                new_date=new_date_str,
                new_time=new_time_str,
                provider_name=provider_name
            )
            
            if success:
                logger.info(f" Reschedule email sent to {patient_email}")
            else:
                logger.error(f" Failed to send reschedule email to {patient_email}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending reschedule email: {str(e)}")
            return False

    def shutdown(self):
        """Gracefully shutdown the scheduler"""
        self.scheduler.shutdown()

# Singleton instance
notification_service = NotificationService()
