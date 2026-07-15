from django.db import models
from receptionist.models import OPDVisit

class LaboratoryRequest(OPDVisit):
    class Meta:
        proxy = True
        verbose_name = "Laboratory Request"
        verbose_name_plural = "Laboratory Requests"
