"""
Email notification utilities for form events.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_form_created_notification(form_type, form_instance, user):
    """
    Send email notification when a form is created.
    
    Args:
        form_type: String identifying the form type (e.g., 'financial_statement_131')
        form_instance: The form model instance that was created
        user: The user who created the form
    """
    try:
        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None)
        if not admin_email:
            logger.warning("ADMIN_NOTIFICATION_EMAIL not configured")
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
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
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
        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', None)
        if not admin_email:
            logger.warning("ADMIN_NOTIFICATION_EMAIL not configured")
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
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Form printed notification sent for {form_type} #{form_instance.pk}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send form printed notification: {e}")
        return False
