"""
Professional Email Templates for EasyAPT
Author: Emil K
"""

def get_appointment_confirmation_email(patient_name, appointment_date, appointment_time, provider_name):
    """Professional appointment confirmation email"""
    
    action_html = ""
    if cancel_url or reschedule_url:
        # Simple button-style links (email safe)
        btn_style = "display:inline-block;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;"
        cancel_btn = f'<a href="{cancel_url}" style="{btn_style}background:#ef4444;color:#ffffff;margin-right:10px;">Cancel Appointment</a>' if cancel_url else ""
        resched_btn = f'<a href="{reschedule_url}" style="{btn_style}background:#2563eb;color:#ffffff;">Reschedule Appointment</a>' if reschedule_url else ""
        action_html = f'''
        <div style="margin: 10px 0 22px 0; text-align:center;">
            {cancel_btn}{resched_btn}
        </div>
        '''

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7fa;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f7fa; padding: 40px 0;">
            <tr>
                <td align="center">
                    <!-- Main Container -->
                    <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                        
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700;">
                                    🏥 EasyAPT
                                </h1>
                                <p style="margin: 10px 0 0 0; color: #ffffff; font-size: 16px; opacity: 0.9;">
                                    Healthcare Appointment Scheduling
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="margin: 0 0 20px 0; color: #2d3748; font-size: 24px; font-weight: 600;">
                                    ✅ Appointment Confirmed
                                </h2>
                                
                                <p style="margin: 0 0 25px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                    Dear <strong>{patient_name}</strong>,
                                </p>
                                
                                <p style="margin: 0 0 30px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                    Your appointment has been successfully scheduled. Here are your appointment details:
                                </p>
                                
                                <!-- Appointment Details Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f7fafc; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 25px;">
                                            <table width="100%" cellpadding="8" cellspacing="0" border="0">
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px; width: 140px;">
                                                        <strong>📅 Date:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; font-weight: 600;">
                                                        {appointment_date}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px;">
                                                        <strong>⏰ Time:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; font-weight: 600;">
                                                        {appointment_time}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px;">
                                                        <strong>👨‍⚕️ Provider:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; font-weight: 600;">
                                                        {provider_name}
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Important Notice -->
                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #edf2f7; border-radius: 8px; margin-bottom: 25px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <p style="margin: 0; color: #2d3748; font-size: 14px; line-height: 1.6;">
                                                <strong>📌 Important Reminders:</strong><br>
                                                • Please arrive 15 minutes before your appointment<br>
                                                • Bring your insurance card and ID<br>
                                                • You will receive a reminder 24 hours before your appointment
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 0 0 20px 0; color: #4a5568; font-size: 14px; line-height: 1.6;">
                                    Need to make changes? Contact our office at <strong>(555) 123-4567</strong> or reply to this email.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #2d3748; padding: 30px; text-align: center;">
                                <p style="margin: 0 0 10px 0; color: #a0aec0; font-size: 14px;">
                                    EasyAPT Healthcare Scheduling Platform
                                </p>
                                <p style="margin: 0; color: #718096; font-size: 12px;">
                                    This is an automated message. Please do not reply directly to this email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html


def get_appointment_cancellation_email(patient_name, appointment_date, appointment_time, provider_name):
    """Professional appointment cancellation email"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7fa;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f7fa; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                        
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #fc8181 0%, #f56565 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700;">
                                    🏥 EasyAPT
                                </h1>
                                <p style="margin: 10px 0 0 0; color: #ffffff; font-size: 16px; opacity: 0.9;">
                                    Healthcare Appointment Scheduling
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="margin: 0 0 20px 0; color: #2d3748; font-size: 24px; font-weight: 600;">
                                    ❌ Appointment Cancelled
                                </h2>
                                
                                <p style="margin: 0 0 25px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                    Dear <strong>{patient_name}</strong>,
                                </p>
                                
                                <p style="margin: 0 0 30px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                    Your appointment has been cancelled as requested. Here were the details:
                                </p>
                                
                                <!-- Cancelled Appointment Details -->
                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fff5f5; border-radius: 8px; border-left: 4px solid #fc8181; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 25px;">
                                            <table width="100%" cellpadding="8" cellspacing="0" border="0">
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px; width: 140px;">
                                                        <strong>📅 Date:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; text-decoration: line-through;">
                                                        {appointment_date}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px;">
                                                        <strong>⏰ Time:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; text-decoration: line-through;">
                                                        {appointment_time}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px;">
                                                        <strong>👨‍⚕️ Provider:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; text-decoration: line-through;">
                                                        {provider_name}
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #edf2f7; border-radius: 8px; margin-bottom: 25px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <p style="margin: 0; color: #2d3748; font-size: 14px; line-height: 1.6;">
                                                <strong>📌 What's Next?</strong><br>
                                                • You can schedule a new appointment anytime<br>
                                                • Visit our website or call (555) 123-4567<br>
                                                • We're here to help you with your healthcare needs
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #2d3748; padding: 30px; text-align: center;">
                                <p style="margin: 0 0 10px 0; color: #a0aec0; font-size: 14px;">
                                    EasyAPT Healthcare Scheduling Platform
                                </p>
                                <p style="margin: 0; color: #718096; font-size: 12px;">
                                    This is an automated message. Please do not reply directly to this email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html


def get_appointment_reminder_email(patient_name, appointment_date, appointment_time, provider_name):
    """Professional appointment reminder email"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0;">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7fa;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f7fa; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                        
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #f6ad55 0%, #ed8936 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700;">
                                    🏥 EasyAPT
                                </h1>
                                <p style="margin: 10px 0 0 0; color: #ffffff; font-size: 16px; opacity: 0.9;">
                                    Healthcare Appointment Scheduling
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="margin: 0 0 20px 0; color: #2d3748; font-size: 24px; font-weight: 600;">
                                    ⏰ Appointment Reminder
                                </h2>
                                
                                <p style="margin: 0 0 25px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                    Dear <strong>{patient_name}</strong>,
                                </p>
                                
                                <p style="margin: 0 0 30px 0; color: #4a5568; font-size: 16px; line-height: 1.6;">
                                    This is a friendly reminder about your upcoming appointment:
                                </p>
                                
                                <!-- Appointment Details Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #fffaf0; border-radius: 8px; border-left: 4px solid #f6ad55; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 25px;">
                                            <table width="100%" cellpadding="8" cellspacing="0" border="0">
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px; width: 140px;">
                                                        <strong>📅 Date:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; font-weight: 600;">
                                                        {appointment_date}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px;">
                                                        <strong>⏰ Time:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; font-weight: 600;">
                                                        {appointment_time}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #718096; font-size: 14px;">
                                                        <strong>👨‍⚕️ Provider:</strong>
                                                    </td>
                                                    <td style="color: #2d3748; font-size: 16px; font-weight: 600;">
                                                        {provider_name}
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Important Notice -->
                                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #edf2f7; border-radius: 8px; margin-bottom: 25px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <p style="margin: 0; color: #2d3748; font-size: 14px; line-height: 1.6;">
                                                <strong>📌 Pre-Appointment Checklist:</strong><br>
                                                • Arrive 15 minutes early<br>
                                                • Bring insurance card and photo ID<br>
                                                • List any medications you're currently taking<br>
                                                • Prepare questions for your provider
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 0 0 20px 0; color: #4a5568; font-size: 14px; line-height: 1.6;">
                                    Need to reschedule? Contact us at <strong>(555) 123-4567</strong> or reply to this email.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #2d3748; padding: 30px; text-align: center;">
                                <p style="margin: 0 0 10px 0; color: #a0aec0; font-size: 14px;">
                                    EasyAPT Healthcare Scheduling Platform
                                </p>
                                <p style="margin: 0; color: #718096; font-size: 12px;">
                                    This is an automated message. Please do not reply directly to this email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
def get_appointment_rescheduled_email(
    patient_name,
    old_date,
    old_time,
    new_date,
    new_time,
    provider_name
):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7fa; padding: 20px;">
        <h2 style="color:#2d3748;">📅 Appointment Rescheduled</h2>

        <p>Hi <strong>{patient_name}</strong>,</p>

        <p>Your appointment with <strong>{provider_name}</strong> has been rescheduled.</p>

        <p>
            <strong>Old:</strong> {old_date} at {old_time}<br>
            <strong>New:</strong> {new_date} at {new_time}
        </p>

        <p>You will receive a reminder before your new appointment.</p>

        <p style="margin-top:30px;">— EasyAPT</p>
    </body>
    </html>
    """
def get_account_created_email(name):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f7fa; padding: 20px;">
        <h2 style="color:#2d3748;">🎉 Welcome to EasyAPT</h2>

        <p>Hi <strong>{name}</strong>,</p>

        <p>Your account has been successfully created.</p>

        <p>If this wasn’t you, please contact support immediately.</p>

        <p style="margin-top:30px;">— EasyAPT</p>
    </body>
    </html>
    """
    
    return html
