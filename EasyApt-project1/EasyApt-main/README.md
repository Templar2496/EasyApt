# EasyApt - Secure Healthcare Appointment Scheduling System

A comprehensive web-based appointment scheduling platform designed with security and HIPAA compliance in mind. Built as a Senior Design Capstone project for Cybersecurity.

## 🎯 Project Overview

EasyApt streamlines healthcare appointment scheduling by providing an intuitive interface for patients to book, reschedule, and cancel appointments while maintaining enterprise-grade security standards.

## ✨ Features

### Patient Features
- 🔐 Secure account registration with strong password requirements
- 📅 Real-time appointment booking with provider search
- ✏️ Easy rescheduling and cancellation
- 👤 Profile management with PHI protection
- 📧 Automated email confirmations and reminders
- 📱 SMS notification support

### Provider Features
- 📊 Comprehensive dashboard with appointment overview
- 👥 Patient information and appointment reason visibility
- 📈 Quick statistics (today's appointments, weekly totals)
- 🗓️ Date-based appointment filtering

### Security Features
- 🔒 Argon2 password hashing (Password Hashing Competition winner)
- 🛡️ Account lockout after 5 failed login attempts (15-minute duration)
- ⏱️ Session timeout after 30 minutes of inactivity
- 💪 Password strength requirements (12+ chars, complexity rules)
- 🤖 CAPTCHA integration (reCAPTCHA v3)
- 🎫 JWT authentication with Bearer tokens
- 👮 Role-based access control

### Communication Features
- 📬 Welcome email on account creation
- ✅ Booking confirmation notifications
- 🔄 Reschedule notifications
- ❌ Cancellation confirmations
- ⏰ 24-hour appointment reminders (automated)

## 🏗️ Architecture

**Three-Tier Architecture:**
- **Frontend:** HTML5, CSS3, JavaScript (ES6 modules)
- **Backend:** FastAPI (Python 3.10+)
- **Database:** PostgreSQL

### Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLModel - SQL database ORM
- Pydantic - Data validation
- python-jose - JWT implementation
- argon2-cffi - Password hashing
- SendGrid - Email service
- Twilio - SMS service
- APScheduler - Task scheduling

**Frontend:**
- Vanilla JavaScript (ES6+)
- Responsive CSS
- Modern HTML5

## 🔒 Security Features

### Password Policy
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

### Account Lockout
- 5 failed login attempts trigger lockout
- 15-minute lockout duration
- Automatic reset on successful login

### Session Management
- 30-minute inactivity timeout
- JWT tokens with 60-minute expiration
- Secure token storage

## 👥 Team

**Project Members:**
- Mason Rasberry - Lead Developer, Frontend, Integration
- Emil K - Security Module, Notifications, 2FA
- Aiden Lambrecht - Backend Dev, Health info
- Jesus Barco - Backend Dev, Login
- Efrain Castaneda-Reyes - Frontend, Captcha

## 📄 License

This project is for educational purposes as part of a Senior Design Capstone course.

## 🙏 Acknowledgments

- University of North Texas - Cybersecurity Program
- FastAPI and SQLModel communities
- Open source security libraries

---

**Note:** This is an educational project. For production deployment, additional security hardening, compliance review, and testing would be required.
