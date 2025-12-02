"""
Notification Service for EasyAPT
Handles SMS and Email notifications for appointments
Author: Emil K
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

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
    Supports both SMS (Twilio) and Email (SendGrid) notifications.
    """
    
    def __init__(self):
        # Twilio configuration
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # SendGrid configuration
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.sendgrid_from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@easyapt.com')
        
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
        
        # Test Mode enabled?
        if os.getenv("TWILIO_TEST_MODE", "false").lower() == "true":
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
        """Send email notification via SendGrid or TEST MODE"""
        
        if os.getenv("MAILTRAP_MODE", "false").lower() == "true":
            logger.info(f"[TEST MODE EMAIL] To: {to_email} | Subject: {subject}\nHTML: {html_content}")
            return True

        if not self.sendgrid_client:
            logger.error("SendGrid client not initialized")
            return False
        
        try:
            message = Mail(
                from_email=self.sendgrid_from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            response = self.sendgrid_client.send(message)
            logger.info(f"Email sent successfully. Status: {response.status_code}")
            return response.status_code in (200, 202)
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
    
    def schedule_reminder(self, patient_phone, patient_email, patient_name, 
                         appointment_date, provider_name, reminder_time):
        """Schedule a reminder notification"""
        try:
            self.scheduler.add_job(
                self.send_appointment_reminder,
                'date',
                run_date=reminder_time,
                args=[patient_phone, patient_email, patient_name, appointment_date, provider_name],
                id=f"reminder_{appointment_date.isoformat()}_{patient_email}",
                replace_existing=True
            )
            logger.info(f"Reminder scheduled for {reminder_time}")
        except Exception as e:
            logger.error(f"Failed to schedule reminder: {str(e)}")
    
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


# Singleton instance
notification_service = NotificationService()
