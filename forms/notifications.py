"""
Email notification utilities for form events.
"""
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def get_email_settings():
    """Get email settings from database or fall back to Django settings."""
    try:
        from .models import EmailSettings
        return EmailSettings.get_settings()
    except Exception:
        return None


def get_email_connection():
    """Get email connection using database settings or default Django settings."""
    email_settings = get_email_settings()
    
    if email_settings and email_settings.email_host:
        # Use database settings
        return get_connection(
            host=email_settings.email_host,
            port=email_settings.email_port,
            username=email_settings.email_host_user,
            password=email_settings.email_host_password,
            use_tls=email_settings.email_use_tls,
            use_ssl=email_settings.email_use_ssl,
        )
    # Use default Django settings
    return None


def get_admin_email():
    """Get admin notification email from database or settings."""
    email_settings = get_email_settings()
    if email_settings and email_settings.admin_notification_email:
        return email_settings.admin_notification_email
    return getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None)


def get_from_email():
    """Get from email from database or settings."""
    email_settings = get_email_settings()
    if email_settings and email_settings.default_from_email:
        return email_settings.default_from_email
    return getattr(settings, 'DEFAULT_FROM_EMAIL', None)


def is_notification_enabled(notification_type='all'):
    """Check if notifications are enabled."""
    try:
        from .models import EmailSettings
        return EmailSettings.is_enabled(notification_type)
    except Exception:
        return True  # Default enabled


def send_form_created_notification(form_type, form_instance, user):
    """
    Send email notification when a form is created.
    
    Args:
        form_type: String identifying the form type (e.g., 'financial_statement_131')
        form_instance: The form model instance that was created
        user: The user who created the form
    """
    try:
        # Check if form creation notifications are enabled
        if not is_notification_enabled('form_create'):
            logger.info("Form creation notifications are disabled")
            return False
        
        admin_email = get_admin_email()
        if not admin_email:
            logger.warning("Admin notification email not configured")
            return False
        
        # Get form display name
        form_names = {
            'financial_statement': 'Financial Statement (Form 13)',
            'financial_statement_131': 'Financial Statement - Property & Support (Form 13.1)',
            'net_family_property_13b': 'Net Family Property (Form 13B)',
            'comparison_nfp': 'Comparison of Net Family Property (Form 13C)',
        }
        form_display_name = form_names.get(form_type, form_type)
        
        # Build applicant name if available
        applicant_name = "N/A"
        if hasattr(form_instance, 'applicant_full_name') and form_instance.applicant_full_name:
            applicant_name = form_instance.applicant_full_name
        elif hasattr(form_instance, 'applicant_first_name') and form_instance.applicant_first_name:
            first = form_instance.applicant_first_name or ''
            last = getattr(form_instance, 'applicant_last_name', '') or ''
            applicant_name = f"{first} {last}".strip() or "N/A"
        
        # Get court file number if available
        court_file = getattr(form_instance, 'court_file_number', 'N/A') or 'N/A'
        
        subject = f"New Form Created: {form_display_name}"
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">📄 New Form Created</h1>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef; border-radius: 0 0 10px 10px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Form Type:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{form_display_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Form ID:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">#{form_instance.pk}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Created By:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{user.username} ({user.email or 'No email'})</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Applicant:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{applicant_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0;"><strong>Court File #:</strong></td>
                            <td style="padding: 10px 0;">{court_file}</td>
                        </tr>
                    </table>
                </div>
                <p style="font-size: 12px; color: #6c757d; margin-top: 20px; text-align: center;">
                    This is an automated notification from Family Law Forms System.
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        connection = get_email_connection()
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=get_from_email(),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
            connection=connection,
        )
        
        logger.info(f"Form created notification sent for {form_type} #{form_instance.pk}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send form created notification: {e}")
        return False


def send_form_printed_notification(form_type, form_instance, user, price_charged=None):
    """
    Send email notification when a form is printed.
    
    Args:
        form_type: String identifying the form type
        form_instance: The form model instance that was printed
        user: The user who printed the form
        price_charged: Optional price charged for the print
    """
    try:
        # Check if form print notifications are enabled
        if not is_notification_enabled('form_print'):
            logger.info("Form print notifications are disabled")
            return False
        
        admin_email = get_admin_email()
        if not admin_email:
            logger.warning("Admin notification email not configured")
            return False
        
        # Get form display name
        form_names = {
            'financial_statement': 'Financial Statement (Form 13)',
            'financial_statement_131': 'Financial Statement - Property & Support (Form 13.1)',
            'net_family_property_13b': 'Net Family Property (Form 13B)',
            'comparison_nfp': 'Comparison of Net Family Property (Form 13C)',
        }
        form_display_name = form_names.get(form_type, form_type)
        
        # Build applicant name if available
        applicant_name = "N/A"
        if hasattr(form_instance, 'applicant_full_name') and form_instance.applicant_full_name:
            applicant_name = form_instance.applicant_full_name
        elif hasattr(form_instance, 'applicant_first_name') and form_instance.applicant_first_name:
            first = form_instance.applicant_first_name or ''
            last = getattr(form_instance, 'applicant_last_name', '') or ''
            applicant_name = f"{first} {last}".strip() or "N/A"
        
        # Get court file number if available
        court_file = getattr(form_instance, 'court_file_number', 'N/A') or 'N/A'
        
        # Price display
        price_display = f"${price_charged:.2f}" if price_charged is not None else "N/A"
        
        subject = f"Form Printed: {form_display_name} #{form_instance.pk}"
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #059669, #047857); padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">🖨️ Form Printed</h1>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef; border-radius: 0 0 10px 10px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Form Type:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{form_display_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Form ID:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">#{form_instance.pk}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Printed By:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{user.username} ({user.email or 'No email'})</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Applicant:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{applicant_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Court File #:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{court_file}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0;"><strong>Price Charged:</strong></td>
                            <td style="padding: 10px 0; color: #059669; font-weight: bold;">{price_display}</td>
                        </tr>
                    </table>
                </div>
                <p style="font-size: 12px; color: #6c757d; margin-top: 20px; text-align: center;">
                    This is an automated notification from Family Law Forms System.
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        connection = get_email_connection()
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=get_from_email(),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
            connection=connection,
        )
        
        logger.info(f"Form printed notification sent for {form_type} #{form_instance.pk}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send form printed notification: {e}")
        return False


def send_login_notification(user, ip_address=None, user_agent=None):
    """
    Send email notification when a user logs in.
    
    Args:
        user: The user who logged in
        ip_address: Optional IP address of the login
        user_agent: Optional user agent string
    """
    try:
        # Check if login notifications are enabled
        if not is_notification_enabled('login'):
            logger.info("Login notifications are disabled")
            return False
        
        admin_email = get_admin_email()
        if not admin_email:
            logger.warning("Admin notification email not configured")
            return False
        
        from django.utils import timezone
        login_time = timezone.now().strftime('%B %d, %Y at %I:%M %p')
        
        subject = f"User Login: {user.username}"
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">🔐 User Login</h1>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border: 1px solid #e9ecef; border-radius: 0 0 10px 10px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Username:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{user.username}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Email:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{user.email or 'Not set'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Full Name:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{user.get_full_name() or 'Not set'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>Login Time:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{login_time}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;"><strong>IP Address:</strong></td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #dee2e6;">{ip_address or 'Unknown'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0;"><strong>User Agent:</strong></td>
                            <td style="padding: 10px 0; font-size: 12px;">{user_agent or 'Unknown'}</td>
                        </tr>
                    </table>
                </div>
                <p style="font-size: 12px; color: #6c757d; margin-top: 20px; text-align: center;">
                    This is an automated notification from Family Law Forms System.
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        connection = get_email_connection()
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=get_from_email(),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
            connection=connection,
        )
        
        logger.info(f"Login notification sent for user {user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send login notification: {e}")
        return False
