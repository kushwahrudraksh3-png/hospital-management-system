from django.urls import path
from . import views

app_name = "receptionist"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("patient-registration/", views.patient_registration, name="patient_registration"),
    path("patient-list/", views.patient_list, name="patient_list"),
    path("patient-summary/", views.patient_summary, name="patient_summary"),
    path("patient-profile/", views.patient_profile, name="patient_profile"),
    path("vitals-entry/", views.vitals_entry, name="vitals_entry"),
    path("opd-registration/", views.opd_registration, name="opd_registration"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("billing/", views.billing, name="billing"),
    path("receipt/", views.receipt, name="receipt"),
    path("opd/receipt/<uuid:patient_id>/", views.opd_receipt, name="opd_receipt"),
]