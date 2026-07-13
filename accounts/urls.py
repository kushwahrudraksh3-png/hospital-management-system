from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("reset-password/", views.reset_password_view, name="reset_password"),
]