import uuid
from django.db import models
from receptionist.models import OPDVisit, Patient

class LabTest(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Laboratory Test Master"
        verbose_name_plural = "Laboratory Test Masters"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (₹{self.price})"

class LaboratoryRequest(OPDVisit):
    class Meta:
        proxy = True
        verbose_name = "Laboratory Request"
        verbose_name_plural = "Laboratory Requests"

class LaboratoryBill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.OneToOneField(
        OPDVisit,
        on_delete=models.CASCADE,
        related_name="laboratory_bill"
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="laboratory_bills"
    )
    bill_number = models.CharField(max_length=50, unique=True, editable=False)
    bill_date = models.DateField(auto_now_add=True)
    bill_time = models.TimeField(auto_now_add=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Laboratory Bill"
        verbose_name_plural = "Laboratory Bills"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.bill_number} - {self.patient.full_name}"

    def save(self, *args, **kwargs):
        if not self.bill_number:
            import datetime
            year = datetime.date.today().year
            count = LaboratoryBill.objects.filter(bill_date__year=year).count()
            self.bill_number = f"LB-{year}-{count + 1:05d}"
            while LaboratoryBill.objects.filter(bill_number=self.bill_number).exists():
                count += 1
                self.bill_number = f"LB-{year}-{count + 1:05d}"
        super().save(*args, **kwargs)

class LaboratoryBillItem(models.Model):
    bill = models.ForeignKey(
        LaboratoryBill,
        on_delete=models.CASCADE,
        related_name="items"
    )
    test = models.ForeignKey(
        LabTest,
        on_delete=models.PROTECT
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} (₹{self.price})"


class LabTestParameter(models.Model):
    """
    Represents an individual parameter for a Laboratory Test.
    Examples:
        - CBC -> Hemoglobin, RBC, WBC, Platelets, etc.
        - LFT -> SGOT, SGPT, Bilirubin, Albumin, etc.
        
    This model is designed to be highly extensible for future enhancements such as:
        - Gender-specific reference ranges (male_reference_range, female_reference_range)
        - Age-specific reference ranges (child_reference_range)
        - Critical value limits (critical_low, critical_high)
        - Parameter categories (e.g. Hematology, Biochemistry)
    """
    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.CASCADE,
        related_name="parameters",
        verbose_name="Laboratory Test"
    )
    parameter_name = models.CharField(max_length=255, verbose_name="Parameter Name")
    unit = models.CharField(max_length=100, blank=True, verbose_name="Unit")
    male_reference_range = models.CharField(max_length=255, blank=True, verbose_name="Male Reference Range")
    female_reference_range = models.CharField(max_length=255, blank=True, verbose_name="Female Reference Range")
    common_reference_range = models.CharField(max_length=255, blank=True, verbose_name="Common Reference Range")
    display_order = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    parameter_type = models.CharField(max_length=100, blank=True, default="Numeric", verbose_name="Parameter Type")
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def clean(self):
        from django.core.exceptions import ValidationError
        
        male = (self.male_reference_range or "").strip()
        female = (self.female_reference_range or "").strip()
        common = (self.common_reference_range or "").strip()
        
        is_gender_specific = bool(male) and bool(female) and not bool(common)
        is_common_only = not bool(male) and not bool(female) and bool(common)
        
        if not (is_gender_specific or is_common_only):
            raise ValidationError(
                "Invalid Reference Range configuration. You must populate EITHER: "
                "1) Both Male and Female Reference Ranges (leaving Common empty) OR "
                "2) Only the Common Reference Range (leaving Male and Female empty)."
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Laboratory Test Parameter"
        verbose_name_plural = "Laboratory Test Parameters"
        ordering = ["display_order", "parameter_name"]

    def __str__(self):
        return f"{self.parameter_name} ({self.lab_test.name})"


class LaboratoryCase(models.Model):
    visit = models.OneToOneField(
        'receptionist.OPDVisit',
        on_delete=models.CASCADE,
        related_name="laboratory_case",
        verbose_name="OPD Visit"
    )
    patient = models.ForeignKey(
        'receptionist.Patient',
        on_delete=models.CASCADE,
        related_name="laboratory_cases",
        verbose_name="Patient"
    )
    case_number = models.CharField(max_length=50, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Laboratory Case"
        verbose_name_plural = "Laboratory Cases"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.case_number:
            import datetime
            year = datetime.date.today().year
            count = LaboratoryCase.objects.filter(created_at__year=year).count()
            self.case_number = f"LC-{year}-{count + 1:05d}"
            while LaboratoryCase.objects.filter(case_number=self.case_number).exists():
                count += 1
                self.case_number = f"LC-{year}-{count + 1:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.case_number} - {self.patient.full_name}"


class LaboratoryReport(models.Model):
    case = models.ForeignKey(
        LaboratoryCase,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="Laboratory Case",
        null=True,
        blank=True
    )
    patient = models.ForeignKey('receptionist.Patient', on_delete=models.CASCADE, related_name="laboratory_reports", verbose_name="Patient")
    visit = models.ForeignKey('receptionist.OPDVisit', on_delete=models.CASCADE, related_name="laboratory_reports", verbose_name="OPD Visit")
    lab_test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name="laboratory_reports", verbose_name="Laboratory Test")
    report_number = models.CharField(max_length=100, unique=True, blank=True, verbose_name="Report Number")
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SENT', 'Sent to Doctor'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Status"
    )
    
    generated_date = models.DateTimeField(auto_now_add=True, verbose_name="Generated Date")
    generated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, verbose_name="Generated By")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Laboratory Report"
        verbose_name_plural = "Laboratory Reports"
        ordering = ["-generated_date"]

    def __str__(self):
        return f"{self.report_number} - {self.lab_test.name} - {self.patient.full_name}"

    def save(self, *args, **kwargs):
        if not self.report_number:
            import datetime
            from django.db import transaction
            year = datetime.date.today().year
            
            with transaction.atomic():
                prefix = f"LR-{year}-"
                last_report = LaboratoryReport.objects.filter(
                    report_number__startswith=prefix
                ).select_for_update().order_by('-report_number').first()
                
                if last_report:
                    try:
                        last_seq = int(last_report.report_number.split('-')[-1])
                        next_seq = last_seq + 1
                    except (ValueError, IndexError):
                        next_seq = 1
                else:
                    next_seq = 1
                
                self.report_number = f"{prefix}{next_seq:05d}"
                while LaboratoryReport.objects.filter(report_number=self.report_number).exists():
                    next_seq += 1
                    self.report_number = f"{prefix}{next_seq:05d}"
                    
        super().save(*args, **kwargs)


class LaboratoryReportResult(models.Model):
    report = models.ForeignKey(LaboratoryReport, on_delete=models.CASCADE, related_name="results", verbose_name="Laboratory Report")
    parameter = models.ForeignKey(LabTestParameter, on_delete=models.CASCADE, related_name="report_results", verbose_name="Parameter")
    result_value = models.CharField(max_length=255, verbose_name="Result Value")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Laboratory Report Result"
        verbose_name_plural = "Laboratory Report Results"
        unique_together = ("report", "parameter")

    def __str__(self):
        return f"{self.parameter.parameter_name}: {self.result_value}"

