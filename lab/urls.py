from django.urls import path
from . import views

app_name = "lab"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
]
