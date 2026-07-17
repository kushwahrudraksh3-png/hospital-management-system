from django.urls import path
from . import views

app_name = "doctor"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("queue/", views.queue, name="queue"),
    path("patient-search/", views.patient_search, name="patient_search"),
    path("patient-summary/", views.patient_summary, name="patient_summary"),
    path("prescription/", views.prescription, name="prescription"),
    path("prescription-preview/", views.prescription_preview, name="prescription_preview"),
    path("prescription-print/", views.prescription_print, name="prescription_print"),
    path("previous-history/", views.previous_history, name="previous_history"),
    path("profile/", views.profile, name="profile"),
    path("report-list/", views.report_list, name="report_list"),
    path("report-view/", views.report_view, name="report_view"),
    path("save-prescription/", views.save_prescription, name="save_prescription"),
    
    path("recommend-ipd/", views.recommend_ipd, name="recommend_ipd"),
    path("ipd-patients/", views.ipd_patients, name="ipd_patients"),
    path("discharge-patient/", views.discharge_patient, name="discharge_patient"),
    
    # Legacy redirect mapping to match existing JavaScript redirects
    path("prescription.html", views.prescription, name="prescription_legacy"),
]