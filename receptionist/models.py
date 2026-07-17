import uuid
from datetime import date
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_dob_not_in_future(value):
    if value > date.today():
        raise ValidationError("Date of birth cannot be in the future.")


class Patient(models.Model):
    class GenderChoices(models.TextChoices):
        FEMALE = "Female", "Female"
        MALE = "Male", "Male"
        OTHER = "Other", "Other"

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Patient Identity
    uhid = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Universal Health Identifier (Auto-generated)"
    )
    full_name = models.CharField(max_length=255, db_index=True)
    father_name = models.CharField(max_length=255, blank=True, null=True)

    # Personal Information
    date_of_birth = models.DateField(validators=[validate_dob_not_in_future])
    gender = models.CharField(
        max_length=10,
        choices=GenderChoices.choices
    )

    # Contact Information
    mobile_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Mobile number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    mobile_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[mobile_validator],
        db_index=True
    )
    address = models.TextField()

    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
        ("Unknown", "Unknown"),
    ]
    blood_group = models.CharField(
        max_length=10,
        choices=BLOOD_GROUP_CHOICES,
        default="Unknown"
    )

    # System Fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients_updated"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.uhid})"

    @property
    def age(self):
        if not self.date_of_birth:
            return ""
        today = date.today()
        dob = self.date_of_birth
        
        if dob > today:
            return ""
            
        years = today.year - dob.year
        months = today.month - dob.month
        days = today.day - dob.day
        
        if days < 0:
            months -= 1
            import calendar
            prev_year = today.year
            prev_month = today.month - 1
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            _, prev_month_days = calendar.monthrange(prev_year, prev_month)
            days += prev_month_days
            
        if months < 0:
            years -= 1
            months += 12
            
        if years >= 1:
            y_str = "1 Year" if years == 1 else f"{years} Years"
            m_str = "1 Month" if months == 1 else f"{months} Months"
            return f"{y_str} {m_str}"
        elif months >= 1:
            return "1 Month" if months == 1 else f"{months} Months"
        else:
            return "1 Day" if days == 1 else f"{days} Days"

    def save(self, *args, **kwargs):
        if not self.uhid:
            with transaction.atomic():
                # Scan last 50 patients chronologically to find the highest number
                patients = Patient.objects.select_for_update().all().order_by('-created_at')[:50]
                max_num = 9999  # Start sequence at 10000 (so first patient is LC-10000)
                for p in patients:
                    if p.uhid and p.uhid.startswith('LC-'):
                        try:
                            num = int(p.uhid.split('-')[1])
                            if num > max_num:
                                max_num = num
                        except (IndexError, ValueError):
                            pass
                next_num = max_num + 1
                
                # Double-check uniqueness to avoid concurrency issues
                while Patient.objects.filter(uhid=f"LC-{next_num:05d}").exists():
                    next_num += 1
                
                self.uhid = f"LC-{next_num:05d}"
        super().save(*args, **kwargs)


class OPDVisit(models.Model):
    class VisitTypeChoices(models.TextChoices):
        NEW_VISIT = "New Visit", "New Visit"
        FOLLOW_UP = "Follow-up", "Follow-up"

    class StatusChoices(models.TextChoices):
        WAITING = "Waiting", "Waiting"
        READY_FOR_DOCTOR = "Ready for Doctor", "Ready for Doctor"
        IN_CONSULTATION = "In Consultation", "In Consultation"
        PENDING_LAB = "Pending Lab", "Pending Lab"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"
        IPD_RECOMMENDED = "IPD Recommended", "IPD Recommended"
        DISCHARGED = "Discharged", "Discharged"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="visits"
    )

    # OPD Visit details
    opd_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True,
        help_text="OPD Identifier (Auto-generated)"
    )
    visit_date = models.DateField(db_index=True)
    visit_time = models.TimeField()
    visit_type = models.CharField(
        max_length=20,
        choices=VisitTypeChoices.choices
    )
    token_number = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.WAITING
    )

    class PaymentModeChoices(models.TextChoices):
        CASH = "Cash", "Cash"
        UPI = "UPI", "UPI"

    payment_mode = models.CharField(
        max_length=10,
        choices=PaymentModeChoices.choices,
        default=PaymentModeChoices.CASH
    )

    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits_updated"
    )

    class Meta:
        ordering = ["-visit_date", "-visit_time"]

    def __str__(self):
        return f"{self.opd_number} - {self.patient.full_name} ({self.visit_date})"

    def save(self, *args, **kwargs):
        if not self.opd_number:
            with transaction.atomic():
                # Scan last 50 visits chronologically to find the highest number
                visits = OPDVisit.objects.select_for_update().all().order_by('-created_at')[:50]
                max_num = 0  # Start sequence at 1
                for v in visits:
                    if v.opd_number and v.opd_number.startswith('OPD-'):
                        try:
                            num = int(v.opd_number.split('-')[1])
                            if num > max_num:
                                max_num = num
                        except (IndexError, ValueError):
                            pass
                next_num = max_num + 1
                
                # Double check uniqueness to avoid concurrency issues
                while OPDVisit.objects.filter(opd_number=f"OPD-{next_num:05d}").exists():
                    next_num += 1
                
                self.opd_number = f"OPD-{next_num:05d}"
        super().save(*args, **kwargs)


class HospitalSettings(models.Model):
    hospital_name = models.CharField(max_length=200)
    hospital_logo = models.ImageField(upload_to='hospital/')
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    opd_validity_days = models.IntegerField(default=10)
    free_followups_allowed = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hospital Settings"
        verbose_name_plural = "Hospital Settings"

    def __str__(self):
        return self.hospital_name


class Vitals(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="vitals_records"
    )
    visit = models.OneToOneField(
        OPDVisit,
        on_delete=models.CASCADE,
        related_name="vitals"
    )
    chief_complaint = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    height = models.DecimalField(
        max_digits=5, decimal_places=1,
        null=True, blank=True,
        help_text="Height in centimetres"
    )
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    heart_rate = models.IntegerField()
    pulse_rate = models.IntegerField(null=True, blank=True)
    blood_pressure = models.CharField(max_length=20)
    spo2 = models.IntegerField()
    respiratory_rate = models.IntegerField(
        null=True, blank=True,
        help_text="Respiratory rate in breaths per minute"
    )
    bottle_feed = models.CharField(
        max_length=3,
        choices=[("Yes", "Yes"), ("No", "No")],
        null=True, blank=True,
        help_text="Whether the patient is on bottle feed"
    )
    blood_group = models.CharField(
        max_length=10,
        choices=Patient.BLOOD_GROUP_CHOICES,
        default="Unknown"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vitals_created"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Vitals"
        verbose_name_plural = "Vitals"

    def __str__(self):
        return f"Vitals for {self.patient.full_name} on {self.created_at.date()}"

