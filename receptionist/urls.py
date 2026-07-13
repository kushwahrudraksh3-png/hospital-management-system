from django.urls import path
from . import views

app_name = "receptionist"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
]