"""
OTP Utility Functions for Voting System
Location: voting/utils.py
FIXED: Removed Unicode characters from logging
"""

import random
import string
import logging
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def generate_otp(length=6):
    """
    Generate a random numeric OTP
    
    Args:
        length (int): Length of OTP (default: 6)
    
    Returns:
        str: Random numeric OTP
    """
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(user_email, otp, purpose="verification"):
    """
    Send OTP via email with professional HTML formatting
    
    Args:
        user_email (str): Recipient email address
        otp (str): The OTP code to send
        purpose (str): Purpose of OTP (verification, login, reset, etc.)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Email subject
        subject = f'Your OTP for Voting System {purpose.title()}'
        
        # Plain text message (fallback)
        plain_message = f"""
Dear Voter,

Your One-Time Password (OTP) for {purpose} is: {otp}

This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes.

If you did not request this OTP, please ignore this email.

Thank you,
Online Voting System Team

---
This is an automated message. Please do not reply to this email.
        """
        
        # HTML message (styled)
        html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OTP Verification</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .email-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .email-header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .email-body {{
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
        }}
        .otp-box {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-left: 4px solid #667eea;
            padding: 25px;
            margin: 30px 0;
            text-align: center;
            border-radius: 8px;
        }}
        .otp-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .otp-code {{
            font-size: 42px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 8px;
            font-family: 'Courier New', monospace;
            margin: 10px 0;
        }}
        .warning-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-left: 4px solid #f39c12;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .warning-box strong {{
            display: block;
            margin-bottom: 5px;
        }}
        .info-text {{
            color: #666;
            font-size: 14px;
            line-height: 1.6;
            margin: 15px 0;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #eee;
        }}
        .divider {{
            height: 1px;
            background: linear-gradient(to right, transparent, #ddd, transparent);
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1>Online Voting System</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">Secure & Transparent Elections</p>
        </div>
        
        <div class="email-body">
            <p class="greeting">Dear Voter,</p>
            
            <p class="info-text">
                You are receiving this email because you requested an OTP for <strong>{purpose}</strong> 
                in the Online Voting System.
            </p>
            
            <div class="otp-box">
                <div class="otp-label">Your One-Time Password</div>
                <div class="otp-code">{otp}</div>
            </div>
            
            <div class="warning-box">
                <strong>Important Information:</strong>
                This OTP will expire in <strong>{settings.OTP_EXPIRY_MINUTES} minutes</strong>. 
                Please use it before it expires.
            </div>
            
            <div class="divider"></div>
            
            <p class="info-text">
                <strong>Security Tips:</strong>
            </p>
            <ul class="info-text">
                <li>Never share your OTP with anyone</li>
                <li>Our team will never ask for your OTP</li>
                <li>If you didn't request this OTP, please ignore this email</li>
            </ul>
            
            <p class="info-text">
                If you have any questions or concerns, please contact our support team.
            </p>
            
            <p class="info-text">
                Thank you for using our secure voting platform!
            </p>
            
            <p class="info-text" style="margin-top: 30px;">
                Best regards,<br>
                <strong>Online Voting System Team</strong>
            </p>
        </div>
        
        <div class="footer">
            <p>This is an automated message from the Online Voting System.</p>
            <p>Please do not reply to this email.</p>
            <p style="margin-top: 10px; font-size: 11px;">
                2026 Online Voting System. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        # Log the attempt (NO UNICODE CHARACTERS)
        logger.info(f"Attempting to send OTP to {user_email} for {purpose}")
        
        # Send the email
        result = send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        
        # Check if email was sent successfully (NO UNICODE CHARACTERS)
        if result == 1:
            logger.info(f"OTP sent successfully to {user_email}")
            return True, "OTP sent successfully! Please check your email."
        else:
            logger.error(f"Failed to send OTP to {user_email} - send_mail returned {result}")
            return False, "Failed to send OTP. Please try again."
    
    except BadHeaderError:
        logger.error(f"Invalid header detected when sending OTP to {user_email}")
        return False, "Invalid email format. Please check your email address."
    
    except ConnectionRefusedError:
        logger.error(f"Connection refused when sending OTP to {user_email}")
        return False, "Email server connection failed. Please contact administrator."
    
    except TimeoutError:
        logger.error(f"Timeout when sending OTP to {user_email}")
        return False, "Email sending timed out. Please try again."
    
    except Exception as e:
        logger.exception(f"Unexpected error sending OTP to {user_email}: {str(e)}")
        return False, f"Error sending OTP: {str(e)}"


def verify_otp(stored_otp, entered_otp, created_at, expiry_minutes=None):
    """
    Verify if the entered OTP matches the stored OTP and hasn't expired
    
    Args:
        stored_otp (str): The OTP stored in database/session
        entered_otp (str): The OTP entered by user
        created_at (datetime): When the OTP was created
        expiry_minutes (int): Minutes until OTP expires (default from settings)
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if expiry_minutes is None:
        expiry_minutes = settings.OTP_EXPIRY_MINUTES
    
    # Check if OTP matches
    if stored_otp != entered_otp:
        logger.warning(f"OTP mismatch - Expected: {stored_otp}, Got: {entered_otp}")
        return False, "Invalid OTP. Please check and try again."
    
    # Check if OTP has expired
    expiry_time = created_at + timedelta(minutes=expiry_minutes)
    current_time = timezone.now()
    
    if current_time > expiry_time:
        logger.warning(f"OTP expired - Created: {created_at}, Expired: {expiry_time}")
        return False, "OTP has expired. Please request a new one."
    
    logger.info("OTP verified successfully")
    return True, "OTP verified successfully"


def test_email_configuration():
    """
    Test function to verify email configuration is working correctly
    
    Usage:
        Run from Django shell:
        >>> python manage.py shell
        >>> from voting.utils import test_email_configuration
        >>> test_email_configuration()
    
    Returns:
        bool: True if email is working, False otherwise
    """
    try:
        print("\n" + "="*60)
        print("  Testing Email Configuration")
        print("="*60 + "\n")
        
        # Get test email
        test_email = settings.EMAIL_HOST_USER
        
        if not test_email:
            print("ERROR: EMAIL_HOST_USER is not configured")
            return False
        
        # Generate test OTP
        test_otp = generate_otp()
        
        print(f"Test Email: {test_email}")
        print(f"Test OTP: {test_otp}")
        print(f"\nSending test email...\n")
        
        # Send test OTP
        success, message = send_otp_email(test_email, test_otp, "test")
        
        if success:
            print("="*60)
            print("  SUCCESS! Email Configuration is Working")
            print("="*60)
            print(f"\n{message}")
            print(f"Check your inbox: {test_email}")
            print("Check spam folder if not in inbox\n")
            return True
        else:
            print("="*60)
            print("  FAILED! Email Configuration Has Issues")
            print("="*60)
            print(f"\nError: {message}\n")
            return False
    
    except Exception as e:
        print("="*60)
        print("  CRITICAL ERROR")
        print("="*60)
        print(f"\nError: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False