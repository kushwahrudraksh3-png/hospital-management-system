from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.dashboard, name='dashboard_root'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # User Management
    path('users/admin/', views.users_admin, name='users_admin'),
    path('users/receptionists/', views.coming_soon, {'title': 'Receptionists'}, name='users_receptionists'),
    path('users/lab/', views.coming_soon, {'title': 'Laboratory Staff'}, name='users_lab'),
    
    # Patient Management
    path('patients/all/', views.patients_all, name='patients_all'),
    path('patients/export/excel/', views.export_patients_excel, name='export_patients_excel'),
    path('patients/export/csv/', views.export_patients_csv, name='export_patients_csv'),
    path('patients/opd/', views.coming_soon, {'title': 'OPD Patients'}, name='patients_opd'),
    path('patients/ipd/', views.coming_soon, {'title': 'IPD Patients'}, name='patients_ipd'),
    path('patients/discharged/', views.coming_soon, {'title': 'Discharged Patients'}, name='patients_discharged'),
    
    # Hospital Masters
    path('masters/ipd/', views.ipd_master, name='ipd_master'),
    path('masters/wards/', views.ipd_master, name='wards'),
    path('masters/rooms/', views.coming_soon, {'title': 'Room Master'}, name='rooms'),
    path('masters/beds/', views.coming_soon, {'title': 'Bed Master'}, name='beds'),
    path('masters/ipd-charges/', views.coming_soon, {'title': 'IPD Charge Master'}, name='ipd_charge_master'),
    path('masters/lab/', views.lab_master, name='lab_master'),
    path('masters/lab-tests/', views.lab_master, name='lab_tests'),
    path('masters/lab-test-parameters/', views.coming_soon, {'title': 'Laboratory Test Parameters'}, name='lab_test_parameters'),
    path('masters/hospital-settings/', views.coming_soon, {'title': 'Hospital Settings'}, name='hospital_information'),
    
    # Billing
    path('billing/opd/', views.coming_soon, {'title': 'OPD Bills'}, name='bills_opd'),
    path('billing/ipd/', views.coming_soon, {'title': 'IPD Bills'}, name='bills_ipd'),
    path('billing/lab/', views.coming_soon, {'title': 'Laboratory Bills'}, name='bills_lab'),
    
    # Reports
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/opd/', views.coming_soon, {'title': 'OPD Report'}, name='reports_opd'),
    path('reports/ipd/', views.coming_soon, {'title': 'IPD Report'}, name='reports_ipd'),
    path('reports/lab/', views.coming_soon, {'title': 'Laboratory Report'}, name='laboratory_reports'),
    path('reports/billing-revenue/', views.reports_dashboard, name='billing_reports'),
    
    # System
    path('system/audit-logs/', views.coming_soon, {'title': 'Audit Logs'}, name='audit_logs'),
    path('system/backup-restore/', views.coming_soon, {'title': 'Database Backup & Restore'}, name='backup_dashboard'),
    path('system/settings/', views.coming_soon, {'title': 'System Settings'}, name='system_settings'),
    
    # Profile
    path('profile/', views.coming_soon, {'title': 'My Profile'}, name='profile'),
    path('profile/change-password/', views.coming_soon, {'title': 'Change Password'}, name='security_settings'),
]
