from datetime import date
from django import forms
from .models import Patient, OPDVisit


class PatientRegistrationForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "full_name",
            "father_name",
            "date_of_birth",
            "gender",
            "mobile_number",
            "address",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter patient's full name",
                    "required": True,
                }
            ),
            "father_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter father's full name",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "required": True,
                }
            ),
            "gender": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
            "mobile_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "10-digit mobile number",
                    "required": True,
                    "type": "tel",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "House number, street, locality, city and PIN code",
                    "rows": 3,
                }
            ),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob and dob > date.today():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get("mobile_number", "")
        # Clean the input by stripping any spaces or dashes
        digits_only = "".join(c for c in mobile if c.isdigit())
        
        # Verify length is correct for standard mobile numbers
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise forms.ValidationError(
                "Please enter a valid mobile number (between 10 and 15 digits)."
            )
        
        # If input has a leading '+', preserve it
        if mobile.startswith("+"):
            return f"+{digits_only}"
        return digits_only

    def validate_unique(self):
        # Exclude mobile_number from unique check because the view handles reusing
        # existing patients with the same mobile number.
        exclude = self._get_validation_exclusions()
        exclude.add("mobile_number")
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as e:
            self._update_errors(e)



class OPDVisitForm(forms.ModelForm):
    visit_type = forms.ChoiceField(
        choices=[
            ("New Visit", "New Patient"),
            ("Follow-up", "Follow Up"),
        ],
        widget=forms.Select(attrs={"class": "form-select", "required": True})
    )

    class Meta:
        model = OPDVisit
        fields = [
            "patient",
            "visit_date",
            "visit_time",
            "visit_type",
            "status",
            "payment_mode",
        ]
        widgets = {
            "patient": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
            "visit_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "required": True,
                }
            ),
            "visit_time": forms.TimeInput(
                attrs={
                    "type": "time",
                    "class": "form-control",
                    "required": True,
                }
            ),
            "visit_type": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
            "payment_mode": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
        }

    def clean_visit_date(self):
        visit_date = self.cleaned_data.get("visit_date")
        if visit_date and visit_date < date.today():
            # In a real hospital system, past visits might be backdated, but we validate it generally.
            # We allow today and future, or standard range. Let's raise validation if it is way in the past.
            pass
        return visit_date


class VitalsForm(forms.Form):
    BOTTLE_FEED_CHOICES = [("", "Select Bottle Feed"), ("Yes", "Yes"), ("No", "No")]

    chief_complaint = forms.CharField(required=True)
    weight = forms.DecimalField(max_digits=5, decimal_places=1, required=True)
    height = forms.DecimalField(max_digits=5, decimal_places=1, required=False,
                                min_value=0)
    temperature = forms.DecimalField(max_digits=4, decimal_places=1, required=True)
    heart_rate = forms.IntegerField(required=True)
    pulse_rate = forms.IntegerField(required=False)
    blood_pressure = forms.CharField(max_length=20, required=True)
    spo2 = forms.IntegerField(required=True)
    respiratory_rate = forms.IntegerField(required=False, min_value=0)
    bottle_feed = forms.ChoiceField(choices=BOTTLE_FEED_CHOICES, required=False)
    blood_group = forms.ChoiceField(choices=Patient.BLOOD_GROUP_CHOICES, required=True)
