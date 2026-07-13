from django import forms
from .models import User

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Email',
            'id': 'email',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Password',
            'id': 'password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'remember_me'
        })
    )

class SignupForm(forms.Form):
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter full name',
            'id': 'full_name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@vatsalyashree.com',
            'id': 'email'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 98765 43210',
            'id': 'phone_number'
        })
    )
    role = forms.ChoiceField(
        choices=[('', 'Select Role')] + list(User.Role.choices),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'role'
        }),
        error_messages={
            'required': 'Please select a role.',
            'invalid_choice': 'Select a valid choice. That choice is not one of the available choices.',
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create password',
            'id': 'password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'id': 'confirm_password'
        })
    )

    def clean_email(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean_phone_number(self):
        import re
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            cleaned = re.sub(r'[\s\-()]', '', phone_number)
            if not re.match(r'^\+?\d{10,15}$', cleaned):
                raise forms.ValidationError("Please enter a valid phone number (10 to 15 digits).")
        return phone_number

    def clean_password(self):
        from django.contrib.auth.password_validation import validate_password
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        return cleaned_data


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@vatsalyashree.com',
            'id': 'email',
            'autocomplete': 'email'
        })
    )

    def clean_email(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            if not User.objects.filter(email=email).exists():
                raise forms.ValidationError("Email does not exist.")
        return email

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.HiddenInput(attrs={'id': 'otp_code'})
    )

class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'id': 'password',
            'autocomplete': 'new-password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'id': 'confirm_password',
            'autocomplete': 'new-password'
        })
    )

    def clean_password(self):
        from django.contrib.auth.password_validation import validate_password
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        return cleaned_data