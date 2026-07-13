import logging

logger = logging.getLogger(__name__)

def send_auth_email(subject, message, recipient_list):
    """
    Reusable email utility for authentication tasks.
    """
    logger.info(f"Sending email to {recipient_list} with subject: {subject}")
    return True


def send_otp_email(recipient_email, otp):
    """
    Sends a password reset OTP email using Django's email utility.
    """
    print("========== OTP EMAIL DEBUG ==========")
    print("Recipient Email:", recipient_email)
    print("OTP:", otp)
    print("=====================================")
    import smtplib
    import socket
    from django.core.mail import send_mail
    from django.conf import settings

    subject = "Password Reset OTP - Vatsalya Shree Hospital"
    message = (
        f"Hello,\n\n"
        f"You have requested a password reset for your Vatsalya Shree Hospital account.\n"
        f"Your OTP code is: {otp}\n"
        f"This OTP is valid for 5 minutes.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"Regards,\n"
        f"Vatsalya Shree Hospital Team"
    )

    try:
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        print("EMAIL SEND RESULT:", result)
        logger.info(f"OTP email sent to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP authentication failure: {e}"
        print(error_msg)
        logger.error(error_msg)
        return False
    except (smtplib.SMTPConnectError, socket.error, OSError) as e:
        error_msg = f"Network issues sending email: {e}"
        print(error_msg)
        logger.error(error_msg)
        return False
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error occurred: {e}"
        print(error_msg)
        logger.error(error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error sending email: {e}"
        print(error_msg)
        logger.error(error_msg)
        return False
