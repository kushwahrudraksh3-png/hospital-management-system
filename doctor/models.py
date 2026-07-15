import uuid
from django.conf import settings
from django.db import models


def prescription_upload_path(instance, filename):
    """Generate compact structured upload path: prescriptions/p_<short_id>/v_<short_id>/prescription.png"""
    short_patient = str(instance.patient_id).replace("-", "")[:8]
    short_visit = str(instance.visit_id).replace("-", "")[:8]
    return f"prescriptions/p_{short_patient}/v_{short_visit}/prescription.png"


class Prescription(models.Model):
    """Stores the handwritten prescription image for a specific OPD visit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    patient = models.ForeignKey(
        "receptionist.Patient",
        on_delete=models.PROTECT,
        related_name="handwritten_prescriptions",
        help_text="Patient this prescription belongs to.",
    )
    visit = models.OneToOneField(
        "receptionist.OPDVisit",
        on_delete=models.PROTECT,
        related_name="handwritten_prescription",
        help_text="OPD Visit this prescription is associated with. One per visit.",
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions_written",
        help_text="Doctor who wrote this prescription.",
    )
    image = models.ImageField(
        upload_to=prescription_upload_path,
        max_length=500,
        help_text="High-quality PNG of the handwritten prescription.",
    )

    snapshot_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Frozen metadata of patient, visit, vitals, doctor, and hospital settings at save time.",
    )
    canvas_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Strokes / JSON / vector data representing the editable master drawing.",
    )

    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prescription for Visit {self.visit_id} (Patient: {self.patient_id})"
