from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from .forms import LoginForm


def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(
                request,
                email=email,
                password=password
            )

            if user is not None:
                login(request, user)

                if user.role == "ADMIN":
                    return redirect("admin:index")

                elif user.role == "RECEPTIONIST":
                    return redirect("receptionist:dashboard")

                elif user.role == "DOCTOR":
                    return redirect("doctor:dashboard")

            messages.error(request, "Invalid email or password.")

    return render(request, "accounts/login.html", {"form": form})