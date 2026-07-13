from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .forms import PatientRegistrationForm, OPDVisitForm
from .models import Patient, OPDVisit


def receptionist_required(view_func):
    """Decorator that checks user is authenticated and has RECEPTIONIST role."""
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib import messages

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "RECEPTIONIST":
            messages.error(request, "Access denied. Receptionist role required.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)
    return wrapper


@receptionist_required
def dashboard(request):
    return render(request, "receptionist/receptionist_dashboard.html", {"active_nav": "dashboard"})


@receptionist_required
def patient_registration(request):
    if request.method == "POST":
        print("[DEBUG] POST request received for patient registration.")
        patient_form = PatientRegistrationForm(request.POST)
        visit_form = OPDVisitForm(request.POST)
        print("[DEBUG] Forms created.")
        
        # Dynamically relax fields processed programmatically on the server
        visit_form.fields['patient'].required = False
        visit_form.fields['visit_date'].required = False
        visit_form.fields['visit_time'].required = False
        visit_form.fields['status'].required = False
        
        patient_valid = patient_form.is_valid()
        visit_valid = visit_form.is_valid()
        print(f"[DEBUG] patient_form.is_valid() = {patient_valid}")
        print(f"[DEBUG] visit_form.is_valid() = {visit_valid}")
        
        if not patient_valid:
            print(f"[DEBUG] patient_form validation errors: {patient_form.errors.as_json()}")
        if not visit_valid:
            print(f"[DEBUG] visit_form validation errors: {visit_form.errors.as_json()}")
            
        if patient_valid and visit_valid:
            try:
                with transaction.atomic():
                    # 1. Reuse existing patient if already present (by mobile number)
                    mobile = patient_form.cleaned_data['mobile_number']
                    patient = Patient.objects.filter(mobile_number=mobile).first()
                    
                    if not patient:
                        print("[DEBUG] Creating new patient.")
                        patient = patient_form.save(commit=False)
                        patient.created_by = request.user
                        patient.updated_by = request.user
                        patient.save()
                        print(f"[DEBUG] New Patient saved with ID: {patient.id}, UHID: {patient.uhid}")
                    else:
                        print(f"[DEBUG] Reusing existing Patient with ID: {patient.id}, UHID: {patient.uhid}")
                    
                    # 2. Create the OPD visit
                    visit = visit_form.save(commit=False)
                    visit.patient = patient
                    
                    # Always assign Visit Date and Visit Time using Django timezone utilities on the server
                    visit.visit_date = timezone.localdate()
                    visit.visit_time = timezone.localtime().time().replace(second=0, microsecond=0)
                    
                    visit.created_by = request.user
                    visit.updated_by = request.user
                    visit.save()
                    print(f"[DEBUG] OPD Visit saved with ID: {visit.id}, OPD Number: {visit.opd_number}")
                    
                messages.success(request, "Patient and OPD registration completed successfully!")
                print(f"[DEBUG] Database transaction committed successfully. Redirecting to receipt page for patient {patient.id}.")
                return redirect('receptionist:opd_receipt', patient_id=patient.id)
                
            except Exception as e:
                print(f"[DEBUG] Exception caught during database save: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"An error occurred while saving registration: {str(e)}")
        else:
            all_errors = []
            for field, errors in patient_form.errors.items():
                all_errors.append(f"Patient Form - {field}: {', '.join(errors)}")
            for field, errors in visit_form.errors.items():
                all_errors.append(f"Visit Form - {field}: {', '.join(errors)}")
            messages.error(request, f"Form validation failed: {'; '.join(all_errors)}")
    else:
        initial_visit = {
            'visit_date': timezone.localdate(),
            'visit_time': timezone.localtime().time().replace(second=0, microsecond=0),
        }
        patient_form = PatientRegistrationForm()
        visit_form = OPDVisitForm(initial=initial_visit)
        
        # Set read-only attributes for fields rendered in UI
        visit_form.fields['visit_date'].widget.attrs['readonly'] = True
        visit_form.fields['visit_time'].widget.attrs['readonly'] = True
        
    context = {
        'patient_form': patient_form,
        'visit_form': visit_form,
        'active_nav': 'patient_registration',
    }
    return render(request, "receptionist/patient_registration.html", context)





@receptionist_required
def patient_list(request):
    return render(request, "receptionist/patient_list.html", {"active_nav": "patient_list"})


@receptionist_required
def patient_summary(request):
    return render(request, "receptionist/patient_summary.html", {"active_nav": "patient_summary"})


@receptionist_required
def patient_profile(request):
    return render(request, "receptionist/patient_profile.html", {"active_nav": "patient_profile"})


@receptionist_required
def vitals_entry(request):
    return render(request, "receptionist/vitals_entry.html", {"active_nav": "vitals_entry"})


@receptionist_required
def opd_registration(request):
    return render(request, "receptionist/opd_registration.html", {"active_nav": "opd_registration"})


@receptionist_required
def edit_profile(request):
    return render(request, "receptionist/edit_profile.html", {"active_nav": "edit_profile"})


@receptionist_required
def billing(request):
    return render(request, "receptionist/billing.html", {"active_nav": "billing"})


@receptionist_required
def receipt(request):
    return render(request, "receptionist/receipt.html", {"active_nav": "receipt"})


@receptionist_required
def opd_receipt(request, patient_id):
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    from receptionist.models import HospitalSettings
    
    patient = get_object_or_404(Patient, id=patient_id)
    visit = OPDVisit.objects.filter(patient=patient).order_by('-visit_date', '-visit_time').first()
    
    hospital = HospitalSettings.objects.first()
    if not hospital:
        hospital = HospitalSettings(
            hospital_name="VATSALYA SHREE HOSPITAL",
            hospital_logo="hospital/hospital_logo.png",
            address="Near Shrinath Talkies, Main Road, Guna (M.P.)",
            phone_number="+91 7542 250000",
            email="contact@vatsalyashree.com",
            consultation_fee=200.00
        )
        
    context = {
        'patient': patient,
        'visit': visit,
        'opd': visit,
        'hospital': hospital,
        'consultation_fee': hospital.consultation_fee,
        'current_datetime': timezone.now(),
        'active_nav': 'receipt',
    }
    return render(request, "receptionist/receipt.html", context)
