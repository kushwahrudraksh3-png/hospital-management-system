from django.urls import path
from . import views

app_name = "receptionist"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("patient-registration/", views.patient_registration, name="patient_registration"),
    path("patient-list/", views.patient_list, name="patient_list"),
    path("patient-summary/", views.patient_summary, name="patient_summary"),
    path("patient-summary/<uuid:patient_id>/", views.patient_summary, name="patient_summary_detail"),
    path("patient-profile/", views.patient_profile, name="patient_profile"),
    path("patient-profile/<uuid:patient_id>/", views.patient_profile, name="patient_profile_detail"),
    path("vitals-entry/", views.vitals_entry, name="vitals_entry"),
    path("vitals-entry/<uuid:patient_id>/", views.vitals_entry, name="vitals_entry_detail"),
    path("edit-latest-vitals/<uuid:patient_id>/", views.edit_latest_vitals, name="edit_latest_vitals"),
    path("opd-registration/", views.opd_registration, name="opd_registration"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("edit-profile/<uuid:patient_id>/", views.edit_profile, name="edit_profile_detail"),
    path("billing/", views.billing, name="billing"),
    path("receipt/", views.receipt, name="receipt"),
    path("opd/receipt/<uuid:patient_id>/", views.opd_receipt, name="opd_receipt"),
    path("opd/create/<uuid:patient_id>/", views.create_opd_visit, name="create_opd_visit"),
    path("received-lab-reports/", views.received_lab_reports, name="received_lab_reports"),
    path("ipd-patients/", views.ipd_patients, name="ipd_patients"),
    path("ipd-registration/", views.ipd_registration, name="ipd_registration"),
    path("ipd-bill/", views.ipd_bill, name="ipd_bill"),
]