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
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    BOOKING_CONFIRMATION = "booking_confirmation"
    APPOINTMENT_REMINDER = "appointment_reminder"
    CANCELLATION = "cancellation"
    RESCHEDULING = "rescheduling"


class NotificationService:
    
    def __init__(self):
        self.twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        self.twilio_phone_number = settings.TWILIO_PHONE_NUMBER
        
        self.sendgrid_api_key = settings.SENDGRID_API_KEY
        self.sendgrid_from_email = settings.SENDGRID_FROM_EMAIL
        
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
        
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        }
        self.scheduler = AsyncIOScheduler(jobstores=jobstores)
        self.scheduler.start()
    
    async def send_sms(self, to_phone: str, message: str) -> bool:
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
        if settings.MAILTRAP_MODE.lower() == "true":
            logger.info(f"[TEST MODE EMAIL] To: {to_email} | Subject: {subject}")
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
        date_str = appointment_date.strftime("%B %d, %Y at %I:%M %p")
        
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
        
        sms_sent = await self.send_sms(patient_phone, sms_message) if patient_phone else False
        email_sent = await self.send_email(patient_email, email_subject, email_html)
        
        return {
            "sms_sent": sms_sent,
            "email_sent": email_sent,
            "reminder_scheduled": False
        }
    async def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email when account is created"""
        
        subject = "Welcome to EasyAPT!"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Welcome to EasyAPT!</h2>
                <p>Dear {name},</p>
                <p>Thank you for creating an account with EasyAPT. Your account has been successfully created.</p>
                <p>You can now:</p>
                <ul>
                    <li>Search for healthcare providers</li>
                    <li>Book appointments online</li>
                    <li>Manage your appointment schedule</li>
                    <li>Update your profile information</li>
                </ul>
                <p>Get started by logging in and booking your first appointment!</p>
                <br>
                <p>Best regards,<br>EasyAPT Team</p>
            </body>
        </html>
        """
        
        return await self.send_email(email, subject, html_content)
    
    async def send_cancellation_email(
        self,
        patient_email: str,
        patient_name: str,
        appointment_date: datetime,
        provider_name: str
    ) -> bool:
        """Send email when appointment is cancelled"""
        
        date_str = appointment_date.strftime("%B %d, %Y at %I:%M %p")
        
        subject = "Appointment Cancelled - EasyAPT"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Appointment Cancelled</h2>
                <p>Dear {patient_name},</p>
                <p>Your appointment has been cancelled:</p>
                <ul>
                    <li><strong>Date &amp; Time:</strong> {date_str}</li>
                    <li><strong>Provider:</strong> {provider_name}</li>
                </ul>
                <p>If you need to schedule a new appointment, please log in to your account.</p>
                <br>
                <p>Best regards,<br>EasyAPT Team</p>
            </body>
        </html>
        """
        
        return await self.send_email(patient_email, subject, html_content)
    
    async def send_reschedule_email(
        self,
        patient_email: str,
        patient_name: str,
        old_date: datetime,
        new_date: datetime,
        provider_name: str
    ) -> bool:
        """Send email when appointment is rescheduled"""
        
        old_date_str = old_date.strftime("%B %d, %Y at %I:%M %p")
        new_date_str = new_date.strftime("%B %d, %Y at %I:%M %p")
        
        subject = "Appointment Rescheduled - EasyAPT"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Appointment Rescheduled</h2>
                <p>Dear {patient_name},</p>
                <p>Your appointment has been successfully rescheduled:</p>
                <ul>
                    <li><strong>Previous Date &amp; Time:</strong> <s>{old_date_str}</s></li>
                    <li><strong>New Date &amp; Time:</strong> <span style="color: #10b981; font-weight: bold;">{new_date_str}</span></li>
                    <li><strong>Provider:</strong> {provider_name}</li>
                </ul>
                <p>You will receive a reminder 24 hours before your appointment.</p>
                <br>
                <p>Best regards,<br>EasyAPT Team</p>
            </body>
        </html>
        """
        
        return await self.send_email(patient_email, subject, html_content)    

    def shutdown(self):
        self.scheduler.shutdown()


notification_service = NotificationService()
