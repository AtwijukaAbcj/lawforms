"""
Django signals for user-related events.
Handles login notifications and audit logging.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

from forms.notifications import send_login_notification

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address from request"""
    if request is None:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Signal handler when a user successfully logs in.
    - Logs the login event to AuditLog
    - Sends email notification
    """
    from .models import AuditLog
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    
    # Create audit log entry
    AuditLog.objects.create(
        user=user,
        action='login',
        module='authentication',
        object_id=str(user.id),
        object_repr=user.username,
        details=f'User logged in successfully',
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    logger.info(f"User {user.username} logged in from {ip_address}")
    
    # Send email notification
    send_login_notification(user, ip_address=ip_address, user_agent=user_agent)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Signal handler when a user logs out.
    - Logs the logout event to AuditLog
    """
    from .models import AuditLog
    
    if user is None:
        return
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    
    # Create audit log entry
    AuditLog.objects.create(
        user=user,
        action='logout',
        module='authentication',
        object_id=str(user.id),
        object_repr=user.username,
        details=f'User logged out',
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    logger.info(f"User {user.username} logged out")


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """
    Signal handler when a login attempt fails.
    - Logs the failed attempt to AuditLog
    """
    from .models import AuditLog
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    username = credentials.get('username', 'unknown')
    
    # Create audit log entry for failed login (no user since login failed)
    AuditLog.objects.create(
        user=None,
        action='login',
        module='authentication',
        object_id='',
        object_repr=username,
        details=f'Failed login attempt for username: {username}',
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    logger.warning(f"Failed login attempt for {username} from {ip_address}")
