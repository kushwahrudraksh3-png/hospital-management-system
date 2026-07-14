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
    from django.utils import timezone
    from datetime import timedelta
    from .models import Patient, OPDVisit
    
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    
    # 1. Today's Patient Metric: Count of unique patients with a visit today
    today_visits = OPDVisit.objects.filter(visit_date=today)
    today_patients_count = today_visits.values('patient').distinct().count()
    
    # Subtext: Today's new patient registrations
    today_new_registrations = Patient.objects.filter(created_at__date=today).count()
    
    # Yesterday's unique patients count for percentage calculation
    yesterday_visits = OPDVisit.objects.filter(visit_date=yesterday)
    yesterday_patients_count = yesterday_visits.values('patient').distinct().count()
    
    # Percentage change for patients
    if yesterday_patients_count > 0:
        patient_percent_change = int(((today_patients_count - yesterday_patients_count) / yesterday_patients_count) * 100)
    else:
        patient_percent_change = 0
    patient_change_abs = abs(patient_percent_change)
    
    # 2. Today's OPD Metric: Count of total OPD visits today
    today_opd_count = today_visits.count()
    
    # Subtext: Number of patients currently waiting
    waiting_opd_count = today_visits.filter(status=OPDVisit.StatusChoices.WAITING).count()
    
    # Yesterday's total OPD visits count for percentage calculation
    yesterday_opd_count = yesterday_visits.count()
    
    # Percentage change for OPD visits
    if yesterday_opd_count > 0:
        opd_percent_change = int(((today_opd_count - yesterday_opd_count) / yesterday_opd_count) * 100)
    else:
        opd_percent_change = 0
    opd_change_abs = abs(opd_percent_change)
    
    # 3. Pending Lab Reports (no model implemented yet, so defaulted to 0 dynamically)
    pending_lab_reports = 0
    lab_reports_due_hour = 0
    
    # 4. Recent Patients table: Retrieve recent OPD visits today or overall
    recent_visits = OPDVisit.objects.select_related('patient').order_by('-visit_date', '-visit_time')[:10]
    
    # Determine appropriate greeting based on time of day
    current_hour = timezone.localtime().hour
    if current_hour < 12:
        greeting_prefix = "Good morning"
    elif current_hour < 17:
        greeting_prefix = "Good afternoon"
    else:
        greeting_prefix = "Good evening"
        
    context = {
        'active_nav': 'dashboard',
        'greeting_prefix': greeting_prefix,
        'today_patients_count': today_patients_count,
        'today_new_registrations': today_new_registrations,
        'patient_percent_change': patient_percent_change,
        'patient_change_abs': patient_change_abs,
        'today_opd_count': today_opd_count,
        'waiting_opd_count': waiting_opd_count,
        'opd_percent_change': opd_percent_change,
        'opd_change_abs': opd_change_abs,
        'pending_lab_reports': pending_lab_reports,
        'lab_reports_due_hour': lab_reports_due_hour,
        'recent_visits': recent_visits,
        'current_time_str': timezone.localtime().strftime("%I:%M %p"),
    }
    return render(request, "receptionist/receptionist_dashboard.html", context)


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
                from django.urls import reverse
                return redirect(f"{reverse('receptionist:opd_receipt', kwargs={'patient_id': patient.id})}?visit_id={visit.id}")
                
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
    from django.db.models import Max, Q
    from django.core.paginator import Paginator
    from django.utils import timezone

    today = timezone.localdate()

    # Base query
    patients_query = Patient.objects.filter(is_active=True)

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        patients_query = patients_query.filter(
            Q(uhid__icontains=q) |
            Q(full_name__icontains=q) |
            Q(mobile_number__icontains=q)
        )

    # Tab filtering
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'today':
        patients_query = patients_query.filter(visits__visit_date=today).distinct()
    elif filter_type == 'new':
        patients_query = patients_query.filter(visits__visit_date=today, visits__visit_type="New Visit").distinct()
    elif filter_type == 'followup':
        patients_query = patients_query.filter(visits__visit_date=today, visits__visit_type="Follow-up").distinct()

    # Sort & Annotate to avoid N+1 query issue
    patients_query = patients_query.annotate(
        latest_visit_date=Max('visits__visit_date')
    ).order_by('-created_at')

    # Pagination: 20 per page
    paginator = Paginator(patients_query, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Dynamic metrics calculation
    total_patients = Patient.objects.filter(is_active=True).count()
    today_visits = OPDVisit.objects.filter(visit_date=today)
    today_patients_count = today_visits.values('patient').distinct().count()
    today_new_count = today_visits.filter(visit_type="New Visit").values('patient').distinct().count()
    today_followup_count = today_visits.filter(visit_type="Follow-up").values('patient').distinct().count()

    context = {
        'page_obj': page_obj,
        'q': q,
        'filter_type': filter_type,
        'total_patients': total_patients,
        'today_patients_count': today_patients_count,
        'today_new_count': today_new_count,
        'today_followup_count': today_followup_count,
        'active_nav': 'patient_list',
    }
    return render(request, "receptionist/patient_list.html", context)


@receptionist_required
def patient_summary(request, patient_id=None):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from .models import Patient, OPDVisit
    
    if patient_id is None:
        patient = Patient.objects.filter(is_active=True).order_by('-created_at').first()
        if not patient:
            messages.warning(request, "No registered patients found.")
            return redirect('receptionist:patient_list')
    else:
        patient = get_object_or_404(Patient, id=patient_id)
        
    latest_visit = patient.visits.order_by('-visit_date', '-visit_time').first()
    
    context = {
        'patient': patient,
        'latest_visit': latest_visit,
        'active_nav': 'patient_list',
    }
    return render(request, "receptionist/patient_summary.html", context)


@receptionist_required
def patient_profile(request):
    return render(request, "receptionist/patient_profile.html", {"active_nav": "patient_profile"})


@receptionist_required
def vitals_entry(request, patient_id=None):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from .models import Patient
    from .forms import VitalsForm
    
    if patient_id is None:
        patient = Patient.objects.filter(is_active=True).order_by('-created_at').first()
        if not patient:
            messages.warning(request, "No registered patients found.")
            return redirect('receptionist:patient_list')
    else:
        patient = get_object_or_404(Patient, id=patient_id)
        
    latest_visit = patient.visits.order_by('-visit_date', '-visit_time').first()
    
    if request.method == "POST":
        form = VitalsForm(request.POST)
        if form.is_valid():
            if not latest_visit:
                messages.error(request, "No OPD Visit found for this patient. Vitals cannot be recorded.")
            else:
                from .models import Vitals, OPDVisit
                Vitals.objects.update_or_create(
                    visit=latest_visit,
                    defaults={
                        'patient': patient,
                        'chief_complaint': form.cleaned_data['chief_complaint'],
                        'weight': form.cleaned_data['weight'],
                        'temperature': form.cleaned_data['temperature'],
                        'heart_rate': form.cleaned_data['heart_rate'],
                        'pulse_rate': form.cleaned_data['pulse_rate'],
                        'blood_pressure': form.cleaned_data['blood_pressure'],
                        'spo2': form.cleaned_data['spo2'],
                        'blood_group': form.cleaned_data['blood_group'],
                        'created_by': request.user
                    }
                )
                patient.blood_group = form.cleaned_data['blood_group']
                patient.save()
                
                # Automatically update OPD Visit status after successful vitals save
                latest_visit.status = OPDVisit.StatusChoices.READY_FOR_DOCTOR
                latest_visit.save()
                
                messages.success(request, "Patient vitals have been saved successfully.")
                return redirect('receptionist:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    
    context = {
        'patient': patient,
        'latest_visit': latest_visit,
        'active_nav': 'patient_list',
    }
    return render(request, "receptionist/vitals_entry.html", context)


@receptionist_required
def edit_latest_vitals(request, patient_id):
    from django.shortcuts import get_object_or_404, redirect, render
    from django.contrib import messages
    from .models import Patient, Vitals, OPDVisit
    from .forms import VitalsForm
    
    patient = get_object_or_404(Patient, id=patient_id)
    vitals = Vitals.objects.filter(patient=patient).order_by('-created_at').first()
    
    if not vitals:
        messages.warning(request, "No Vitals record found for this patient.")
        return redirect('receptionist:patient_summary_detail', patient_id=patient.id)
        
    latest_visit = vitals.visit
    
    if request.method == "POST":
        form = VitalsForm(request.POST)
        if form.is_valid():
            vitals.chief_complaint = form.cleaned_data['chief_complaint']
            vitals.weight = form.cleaned_data['weight']
            vitals.temperature = form.cleaned_data['temperature']
            vitals.heart_rate = form.cleaned_data['heart_rate']
            vitals.pulse_rate = form.cleaned_data['pulse_rate']
            vitals.blood_pressure = form.cleaned_data['blood_pressure']
            vitals.spo2 = form.cleaned_data['spo2']
            vitals.blood_group = form.cleaned_data['blood_group']
            vitals.save()
            
            patient.blood_group = form.cleaned_data['blood_group']
            patient.save()
            
            # Automatically update OPD Visit status after successful vitals save
            if latest_visit:
                latest_visit.status = OPDVisit.StatusChoices.READY_FOR_DOCTOR
                latest_visit.save()
                
            messages.success(request, "Patient vitals have been updated successfully.")
            return redirect('receptionist:patient_summary_detail', patient_id=patient.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
                    
    context = {
        'patient': patient,
        'latest_visit': latest_visit,
        'vitals': vitals,
        'is_edit': True,
        'active_nav': 'patient_list',
    }
    return render(request, "receptionist/vitals_entry.html", context)


@receptionist_required
def opd_registration(request):
    return render(request, "receptionist/opd_registration.html", {"active_nav": "opd_registration"})


@receptionist_required
def edit_profile(request, patient_id=None):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from .models import Patient
    
    if patient_id is None:
        patient = Patient.objects.filter(is_active=True).order_by('-created_at').first()
        if not patient:
            messages.warning(request, "No registered patients found.")
            return redirect('receptionist:patient_list')
    else:
        patient = get_object_or_404(Patient, id=patient_id)
        
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        father_name = request.POST.get('father_name')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        mobile_number = request.POST.get('mobile_number')
        address = request.POST.get('address')
        
        if not full_name or not date_of_birth or not gender or not mobile_number:
            messages.error(request, "Required fields are missing.")
        else:
            try:
                from datetime import datetime
                dob_date = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
                patient.full_name = full_name
                patient.father_name = father_name
                patient.date_of_birth = dob_date
                patient.gender = gender
                
                digits_only = "".join(c for c in mobile_number if c.isdigit())
                if len(digits_only) < 10 or len(digits_only) > 15:
                    messages.error(request, "Please enter a valid mobile number (between 10 and 15 digits).")
                else:
                    patient.mobile_number = digits_only
                    patient.address = address
                    patient.save()
                    messages.success(request, f"Patient profile for {patient.full_name} updated successfully!")
                    return redirect('receptionist:patient_summary_detail', patient_id=patient.id)
            except Exception as e:
                messages.error(request, f"Error saving patient details: {str(e)}")
                
    context = {
        'patient': patient,
        'active_nav': 'patient_list',
    }
    return render(request, "receptionist/edit_profile.html", context)


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
    visit_id = request.GET.get('visit_id')
    if visit_id:
        visit = get_object_or_404(OPDVisit, id=visit_id)
        if visit.patient_id != patient.id:
            visit = OPDVisit.objects.filter(patient=patient).order_by('-visit_date', '-visit_time').first()
    else:
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


@receptionist_required
def create_opd_visit(request, patient_id):
    if request.method == "POST":
        from django.shortcuts import get_object_or_404
        from django.urls import reverse
        from django.contrib import messages
        from django.utils import timezone
        from .models import Patient, OPDVisit
        
        patient = get_object_or_404(Patient, id=patient_id)
        payment_mode = request.POST.get('payment_mode')
        
        if not payment_mode or payment_mode not in ['CASH', 'UPI']:
            messages.error(request, "Invalid or missing Payment Mode.")
            return redirect('receptionist:patient_list')
            
        with transaction.atomic():
            # Create a new OPD visit
            visit = OPDVisit(
                patient=patient,
                visit_date=timezone.localdate(),
                visit_time=timezone.localtime().time().replace(second=0, microsecond=0),
                visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
                status=OPDVisit.StatusChoices.WAITING,
                payment_mode=payment_mode,
                created_by=request.user,
                updated_by=request.user
            )
            visit.save()
        
        messages.success(request, f"New OPD visit created successfully for {patient.full_name}!")
        return redirect(f"{reverse('receptionist:opd_receipt', kwargs={'patient_id': patient.id})}?visit_id={visit.id}")
        
    return redirect('receptionist:patient_list')
