import logging
import os
import json
from datetime import datetime
from django.conf import settings

# Ensure logs directory exists
LOGS_DIR = os.path.join(settings.BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure Audit Logger
audit_logger = logging.getLogger('hms_audit')
audit_logger.setLevel(logging.INFO)
audit_handler = logging.FileHandler(os.path.join(LOGS_DIR, 'audit.log'))
audit_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
audit_handler.setFormatter(audit_formatter)
if not audit_logger.handlers:
    audit_logger.addHandler(audit_handler)

# Configure Error Logger
error_logger = logging.getLogger('hms_error')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler(os.path.join(LOGS_DIR, 'error.log'))
error_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
error_handler.setFormatter(error_formatter)
if not error_logger.handlers:
    error_logger.addHandler(error_handler)


def get_client_ip(request):
    """Extract client IP address safely from request META."""
    if not request:
        return '127.0.0.1'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def get_user_role(user):
    """Determine user role safely."""
    if not user or not user.is_authenticated:
        return 'Anonymous'
    if user.is_superuser:
        return 'Super Admin'
    if hasattr(user, 'role'):
        return str(user.role)
    if user.groups.exists():
        return user.groups.first().name
    return 'Staff'


def log_audit_activity(request, module, action, record_id="", details=""):
    """
    Automatically record every important activity with user, role, module, action, record ID, IP, and timestamp.
    """
    try:
        user = request.user if request and hasattr(request, 'user') else None
        username = user.username if user and user.is_authenticated else 'System'
        role = get_user_role(user)
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown') if request else 'Unknown'

        log_payload = {
            'timestamp': datetime.now().isoformat(),
            'user': username,
            'role': role,
            'module': module,
            'action': action,
            'record_id': str(record_id),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'details': details
        }
        
        audit_logger.info(json.dumps(log_payload))
    except Exception as e:
        error_logger.error(f"Failed to write audit log: {str(e)}")


def log_exception(request, exception, details=""):
    """Log unexpected errors securely without exposing stack traces to normal users."""
    try:
        user = request.user.username if request and hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
        url = request.build_absolute_uri() if request else 'Unknown URL'
        ip_address = get_client_ip(request)
        
        error_payload = {
            'timestamp': datetime.now().isoformat(),
            'user': user,
            'url': url,
            'ip_address': ip_address,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'details': details
        }
        
        error_logger.error(json.dumps(error_payload))
    except Exception as e:
        error_logger.error(f"Failed to write error log: {str(e)}")


def is_record_locked(instance, user):
    """
    Check if a record (Bill, Prescription, Lab Report) is locked.
    Finalized records are locked for normal users, editable only by Super Admin.
    """
    if not instance:
        return False
    if user and user.is_superuser:
        return False  # Super Admin can edit
    
    status = getattr(instance, 'status', None)
    if status in ['Final', 'Paid', 'Completed', 'Discharged', 'Locked']:
        return True
    return False
