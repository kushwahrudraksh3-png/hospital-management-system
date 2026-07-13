def check_password_strength(password):
    """
    Helper function to check password strength.
    """
    return len(password) >= 8


def generate_otp():
    """
    Generates a secure 6-digit OTP code as a string.
    """
    import secrets
    return str(secrets.randbelow(900000) + 100000)
