from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils import timezone
import datetime
import logging

from .forms import LoginForm, SignupForm, ForgotPasswordForm, OTPVerificationForm, ResetPasswordForm
from .models import User, PasswordResetOTP
from .utils import generate_otp
from .emailer import send_otp_email

logger = logging.getLogger(__name__)


def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            remember_me = form.cleaned_data.get("remember_me", False)

            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)

                if remember_me:
                    request.session.set_expiry(None)  # Browser-length session
                else:
                    request.session.set_expiry(0)     # Expires on browser close

                if user.role == "ADMIN":
                    return redirect("admin:index")
                elif user.role == "RECEPTIONIST":
                    return redirect("receptionist:dashboard")
                elif user.role == "DOCTOR":
                    return redirect("doctor:dashboard")
                elif user.role == "LAB_ADMINISTRATOR":
                    return redirect("lab:dashboard")
                else:
                    return redirect("accounts:login")

            messages.error(request, "Invalid email or password.")

    return render(request, "accounts/login.html", {"form": form})


def signup_view(request):
    form = SignupForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            full_name = form.cleaned_data["full_name"]
            email = form.cleaned_data["email"]
            phone_number = form.cleaned_data["phone_number"]
            role = form.cleaned_data["role"]
            password = form.cleaned_data["password"]

            # Split full_name into first_name and last_name
            name_parts = full_name.strip().split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Generate a unique username from email
            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                role=role,
                is_active=True,
                is_staff=False,
            )
            user.set_password(password)
            user.save()

            messages.success(request, "Account created successfully. Please login.")
            return redirect("accounts:login")

    return render(request, "accounts/signup.html", {"form": form})


def forgot_password_view(request):
    form = ForgotPasswordForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data["email"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                form.add_error("email", "Email does not exist.")
                return render(request, "accounts/forgot_password.html", {"form": form})

            # Invalidate previous OTPs
            PasswordResetOTP.objects.filter(user=user).delete()

            # Generate and save new OTP
            otp = generate_otp()
            expires_at = timezone.now() + datetime.timedelta(minutes=5)
            PasswordResetOTP.objects.create(
                user=user,
                otp_code=otp,
                expires_at=expires_at,
            )

            logger.info(f"Generated OTP for {user.email}: {otp}")

            email_sent = send_otp_email(user.email, otp)

            if not email_sent:
                messages.error(request, "Failed to send OTP email. Please try again.")
                return render(request, "accounts/forgot_password.html", {"form": form})

            # Store email in session for subsequent views
            request.session["password_reset_email"] = user.email

            messages.success(request, "OTP has been sent to your registered email.")
            return redirect("accounts:verify_otp")

    return render(request, "accounts/forgot_password.html", {"form": form})


def verify_otp_view(request):
    if not request.session.get("password_reset_email"):
        messages.error(request, "Please enter your email to request an OTP.")
        return redirect("accounts:forgot_password")

    form = OTPVerificationForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            otp_entered = form.cleaned_data["otp"]
            email = request.session.get("password_reset_email")

            if not email:
                messages.error(request, "Session expired. Please request a new OTP.")
                return redirect("accounts:forgot_password")

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "User not found. Please request a new OTP.")
                return redirect("accounts:forgot_password")

            otp_record = PasswordResetOTP.objects.filter(
                user=user, is_verified=False
            ).last()

            if not otp_record or otp_record.otp_code != otp_entered:
                form.add_error("otp", "Invalid OTP. Please try again.")
                return render(request, "accounts/verify_otp.html", {"form": form})

            if otp_record.is_expired():
                form.add_error("otp", "OTP has expired. Please request a new one.")
                return render(request, "accounts/verify_otp.html", {"form": form})

            # Mark OTP as verified
            otp_record.is_verified = True
            otp_record.save()

            request.session["otp_verified"] = True

            return redirect("accounts:reset_password")

    return render(request, "accounts/verify_otp.html", {"form": form})


def reset_password_view(request):
    email = request.session.get("password_reset_email")
    otp_verified = request.session.get("otp_verified")

    if not email or not otp_verified:
        messages.error(request, "Please verify your OTP first.")
        return redirect("accounts:forgot_password")

    form = ResetPasswordForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "User not found. Please start over.")
                return redirect("accounts:forgot_password")

            new_password = form.cleaned_data["password"]
            user.set_password(new_password)
            user.save()

            # Cleanup OTPs and session flags
            PasswordResetOTP.objects.filter(user=user).delete()
            request.session.pop("password_reset_email", None)
            request.session.pop("otp_verified", None)

            messages.success(request, "Password reset successfully. Please login.")
            return redirect("accounts:login")

    return render(request, "accounts/reset_password.html", {"form": form})