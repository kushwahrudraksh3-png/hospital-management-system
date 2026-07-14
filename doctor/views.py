from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, "doctor/dashboard.html", {"active_nav": "dashboard"})


@login_required
def queue(request):
    return render(request, "doctor/queue.html", {"active_nav": "queue"})


@login_required
def patient_search(request):
    return render(request, "doctor/patient_search.html", {"active_nav": "patient_search"})


@login_required
def patient_summary(request):
    return render(request, "doctor/patient_summary.html", {"active_nav": "patient_search"})


@login_required
def prescription(request):
    return render(request, "doctor/prescription.html", {"active_nav": "queue"})


@login_required
def prescription_preview(request):
    return render(request, "doctor/prescription_preview.html", {"active_nav": "queue"})


@login_required
def prescription_print(request):
    return render(request, "doctor/prescription_print.html", {"active_nav": "queue"})


@login_required
def previous_history(request):
    return render(request, "doctor/previous_history.html", {"active_nav": "queue"})


@login_required
def profile(request):
    return render(request, "doctor/profile.html", {"active_nav": "profile"})


@login_required
def report_list(request):
    return render(request, "doctor/report_list.html", {"active_nav": "report_list"})


@login_required
def report_view(request):
    return render(request, "doctor/report_view.html", {"active_nav": "report_list"})
