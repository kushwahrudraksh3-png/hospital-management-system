from django.urls import path
from . import views

app_name = "lab"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("todays-patients/", views.todays_patients, name="todays_patients"),
    path("completed-reports/", views.completed_reports, name="completed_reports"),
    path("billing/", views.lab_billing, name="lab_billing"),
    path("receipt/", views.bill_receipt, name="bill_receipt"),
    path("total-billing-patients/", views.total_billing_patients, name="total_billing_patients"),
    path("report-entry/", views.report_entry, name="report_entry"),
    path("report-entry/save/", views.report_save, name="report_save"),
    path("report-preview/", views.report_preview, name="report_preview"),
    path("doctor-prescription/", views.doctor_prescription, name="doctor_prescription"),
]
