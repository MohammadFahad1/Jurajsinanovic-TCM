from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

@shared_task
def send_activation_otp_email(email, otp):
    subject = "OTP - Activate Your Prune Account"
    from_email = settings.CUSTOM_EMAIL_SENDER 
    
    context = {"otp": otp, "purpose": "Activation"}
    html_content = render_to_string("otp_template.html", context)
    text_content = strip_tags(html_content)
    try:
        msg = EmailMultiAlternatives(
            subject, 
            text_content, 
            from_email, 
            [email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        return f'Email sent to {email}'
    except Exception as e:
        return f'Error: {e}'


@shared_task
def send_two_fa_otp_email(email, otp):
    subject = "OTP - Two-Factor Authentication for Prune"
    from_email = settings.CUSTOM_EMAIL_SENDER 
    
    context = {"otp": otp, "purpose": "Two-Factor Authentication"}
    html_content = render_to_string("otp_template.html", context)
    text_content = strip_tags(html_content)
    try:
        msg = EmailMultiAlternatives(
            subject, 
            text_content, 
            from_email, 
            [email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        return f'Email sent to {email}'
    except Exception as e:
        return f'Error: {e}'

@shared_task
def send_reset_otp_email(email, otp):
    subject = "OTP - Reset Your Prune Password"
    from_email = settings.CUSTOM_EMAIL_SENDER 
    
    context = {"otp": otp, "purpose": "Password Reset"}
    html_content = render_to_string("otp_template.html", context)
    text_content = strip_tags(html_content)
    try:
        msg = EmailMultiAlternatives(
            subject, 
            text_content, 
            from_email, 
            [email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        msg.send()
        return f'Email sent to {email}'
    except Exception as e:
        return f'Error: {e}'

@shared_task
def send_guide_credentials_email(email, full_name, password):
    subject = "Your Tour Guide Account Credentials - Prune"
    from_email = getattr(settings, 'CUSTOM_EMAIL_SENDER', 'noreply@Prune.com')
    
    context = {
        "full_name": full_name,
        "email": email,
        "password": password,
        "login_url": getattr(settings, 'GUIDE_LOGIN_URL', 'https://Prune.com/login')
    }
    html_content = render_to_string("guide_credentials_template.html", context)
    text_content = strip_tags(html_content)
    try:
        msg = EmailMultiAlternatives(
            subject, 
            text_content, 
            from_email, 
            [email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return f'Email sent to {email}'
    except Exception as e:
        return f'Error: {e}'

def dispatch_guide_credentials_email(email, full_name, password):
    """
    Safely dispatches guide credentials email using Celery delay if available,
    falling back to synchronous invocation (and executing synchronously during tests).
    """
    import sys
    if 'test' in sys.argv:
        send_guide_credentials_email(email, full_name, password)
    else:
        try:
            send_guide_credentials_email.delay(email, full_name, password)
        except Exception:
            send_guide_credentials_email(email, full_name, password)