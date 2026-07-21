from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .forms import PatientRegistrationForm, OPDVisitForm
from .models import Patient, OPDVisit, HospitalSettings


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
    from datetime import timedelta, datetime
    from .models import Patient, OPDVisit
    
    today = timezone.localdate()
    
    # Parse and validate selected date
    date_str = request.GET.get('date')
    selected_date = today
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    previous_day = selected_date - timedelta(days=1)
    
    # 1. Patient Metric: Count of unique patients with a visit on selected date
    selected_visits = OPDVisit.objects.filter(visit_date=selected_date)
    patients_count = selected_visits.values('patient').distinct().count()
    
    # Subtext: Selected date's new patient registrations
    new_registrations = Patient.objects.filter(created_at__date=selected_date).count()
    
    # Previous day's unique patients count for percentage calculation
    previous_visits = OPDVisit.objects.filter(visit_date=previous_day)
    previous_patients_count = previous_visits.values('patient').distinct().count()
    
    # Percentage change for patients
    if previous_patients_count > 0:
        patient_percent_change = int(((patients_count - previous_patients_count) / previous_patients_count) * 100)
    else:
        patient_percent_change = 0
    patient_change_abs = abs(patient_percent_change)
    
    # 2. OPD Metric: Count of total OPD visits on selected date
    opd_count = selected_visits.filter(visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT).count()
    
    # Subtext: Number of patients currently waiting on selected date
    waiting_opd_count = selected_visits.filter(status=OPDVisit.StatusChoices.WAITING).count()
    
    # Previous day's total OPD visits count for percentage calculation
    previous_opd_count = previous_visits.filter(visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT).count()
    
    # Percentage change for OPD visits
    if previous_opd_count > 0:
        opd_percent_change = int(((opd_count - previous_opd_count) / previous_opd_count) * 100)
    else:
        opd_percent_change = 0
    opd_change_abs = abs(opd_percent_change)
    
    # 3. Pending Lab Reports (excluding visits where all lab reports are completed/sent)
    from lab.models import LaboratoryReport
    completed_visit_ids = LaboratoryReport.objects.filter(
        visit__in=selected_visits,
        status__in=['COMPLETED', 'SENT']
    ).exclude(
        visit__laboratory_reports__status__in=['PENDING', 'IN_PROGRESS']
    ).values_list('visit_id', flat=True)

    pending_lab_reports = selected_visits.filter(
        Q(status=OPDVisit.StatusChoices.PENDING_LAB) |
        Q(laboratory_reports__isnull=False)
    ).exclude(
        id__in=completed_visit_ids
    ).distinct().count()
    lab_reports_due_hour = 0
    
    # 4. Recent Patients table: Retrieve recent OPD visits on selected date
    recent_visits = OPDVisit.objects.filter(visit_date=selected_date).select_related('patient').order_by('-visit_time')[:10]
    
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
        'today_patients_count': patients_count,
        'today_new_registrations': new_registrations,
        'patient_percent_change': patient_percent_change,
        'patient_change_abs': patient_change_abs,
        'today_opd_count': opd_count,
        'waiting_opd_count': waiting_opd_count,
        'opd_percent_change': opd_percent_change,
        'opd_change_abs': opd_change_abs,
        'pending_lab_reports': pending_lab_reports,
        'lab_reports_due_hour': lab_reports_due_hour,
        'recent_visits': recent_visits,
        'current_time_str': timezone.localtime().strftime("%I:%M %p"),
        'selected_date': selected_date,
        'today': today,
    }
    return render(request, "receptionist/receptionist_dashboard.html", context)


def determine_visit_type(patient, hospital):
    from django.utils import timezone
    from receptionist.models import OPDVisit
    
    today = timezone.localdate()
    
    # Step 1: Find the patient's latest PAID OPD (visit_type = "New Visit")
    latest_paid_opd = OPDVisit.objects.filter(
        patient=patient,
        visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT
    ).order_by('-visit_date', '-visit_time').first()
    
    if latest_paid_opd:
        validity_days = hospital.opd_validity_days
        days_passed = (today - latest_paid_opd.visit_date).days
        
        if 0 <= days_passed < validity_days:
            # Active validity window
            # Check how many follow-ups have been used since that latest paid OPD visit_date
            followups_count = OPDVisit.objects.filter(
                patient=patient,
                visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
                visit_date__gte=latest_paid_opd.visit_date
            ).count()
            
            if followups_count < hospital.free_followups_allowed:
                # Allowed to have a free follow-up
                return OPDVisit.VisitTypeChoices.FOLLOW_UP
    
    # Otherwise, it's a new paid OPD cycle
    return OPDVisit.VisitTypeChoices.NEW_VISIT


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
        visit_form.fields['visit_type'].required = False
        
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
                    # 1. Create new patient record for registration
                    patient = patient_form.save(commit=False)
                    patient.created_by = request.user
                    patient.updated_by = request.user
                    patient.save()
                    is_new_patient = True
                    print(f"[DEBUG] New Patient saved with ID: {patient.id}, UHID: {patient.uhid}")
                    
                    # 2. Create the OPD visit
                    visit = visit_form.save(commit=False)
                    visit.patient = patient
                    visit.visit_type = OPDVisit.VisitTypeChoices.NEW_VISIT
                    
                    # Always assign Visit Date and Visit Time using Django timezone utilities on the server
                    visit.visit_date = timezone.localdate()
                    visit.visit_time = timezone.localtime().time().replace(second=0, microsecond=0)
                    
                    visit.created_by = request.user
                    visit.updated_by = request.user
                    visit.save()
                    print(f"[DEBUG] OPD Visit saved with ID: {visit.id}, OPD Number: {visit.opd_number}")
                    
                messages.success(request, "Patient and OPD registration completed successfully!")
                print(f"[DEBUG] Database transaction committed successfully. Redirecting...")
                if visit.visit_type == OPDVisit.VisitTypeChoices.NEW_VISIT or is_new_patient:
                    return redirect(f"{reverse('receptionist:opd_receipt', kwargs={'patient_id': patient.id})}?visit_id={visit.id}")
                else:
                    return redirect(f"{reverse('receptionist:vitals_entry_detail', kwargs={'patient_id': patient.id})}?visit_id={visit.id}")
                
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

    # Date filter
    date_str = request.GET.get('date', '').strip()
    selected_date = None
    if date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Tab and Date filtering
    filter_type = request.GET.get('filter', 'all')
    if selected_date:
        if filter_type == 'all':
            patients_query = patients_query.filter(
                Q(created_at__date=selected_date) | Q(visits__visit_date=selected_date)
            ).distinct()
        elif filter_type == 'today':
            patients_query = patients_query.filter(visits__visit_date=selected_date).distinct()
        elif filter_type == 'new':
            patients_query = patients_query.filter(visits__visit_date=selected_date, visits__visit_type="New Visit").distinct()
        elif filter_type == 'followup':
            patients_query = patients_query.filter(visits__visit_date=selected_date, visits__visit_type="Follow-up").distinct()
    else:
        if filter_type == 'today':
            patients_query = patients_query.filter(visits__visit_date=today).distinct()
        elif filter_type == 'new':
            patients_query = patients_query.filter(visits__visit_date=today, visits__visit_type="New Visit").distinct()
        elif filter_type == 'followup':
            patients_query = patients_query.filter(visits__visit_date=today, visits__visit_type="Follow-up").distinct()

    # Sort & Annotate to avoid N+1 query issue
    from django.db.models import Count
    patients_query = patients_query.annotate(
        latest_visit_date=Max('visits__visit_date'),
        followup_count=Count('visits', filter=Q(visits__visit_type="Follow-up"))
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
        'date_str': date_str,
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
    from doctor.models import Prescription
    
    if patient_id is None:
        patient = Patient.objects.filter(is_active=True).order_by('-created_at').first()
        if not patient:
            messages.warning(request, "No registered patients found.")
            return redirect('receptionist:patient_list')
    else:
        patient = get_object_or_404(Patient, id=patient_id)
        
    visit_id = request.GET.get('visit_id')
    if visit_id:
        latest_visit = patient.visits.filter(id=visit_id).first()
        if not latest_visit:
            latest_visit = patient.visits.order_by('-visit_date', '-visit_time').first()
    else:
        latest_visit = patient.visits.order_by('-visit_date', '-visit_time').first()

    prescription = None
    if latest_visit:
        prescription = Prescription.objects.filter(patient=patient, visit=latest_visit).first()
    
    context = {
        'patient': patient,
        'latest_visit': latest_visit,
        'prescription': prescription,
        'active_nav': 'patient_list',
    }
    return render(request, "receptionist/patient_summary.html", context)


@receptionist_required
def patient_profile(request, patient_id=None):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from .models import Patient, OPDVisit, Vitals
    from doctor.models import Prescription
    from lab.models import LaboratoryBill
    
    if patient_id is None:
        patient_id = request.GET.get('patient_id')
        
    if patient_id is None:
        patient = Patient.objects.filter(is_active=True).order_by('-created_at').first()
        if not patient:
            messages.warning(request, "No registered patients found.")
            return redirect('receptionist:patient_list')
    else:
        patient = get_object_or_404(Patient, id=patient_id)
        
    visits = patient.visits.all().order_by('-visit_date', '-visit_time')
    latest_visit = visits.first()
    
    latest_vitals = Vitals.objects.filter(patient=patient).order_by('-created_at').first()
    
    bmi = None
    if latest_vitals and latest_vitals.weight and latest_vitals.height:
        try:
            height_m = float(latest_vitals.height) / 100.0
            weight_kg = float(latest_vitals.weight)
            if height_m > 0:
                bmi = round(weight_kg / (height_m ** 2), 2)
        except (ValueError, TypeError):
            pass
            
    latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()
    
    latest_opd_visit = visits.filter(status=OPDVisit.StatusChoices.COMPLETED).first()
    if not latest_opd_visit:
        latest_opd_visit = latest_visit
        
    latest_lab_bill = LaboratoryBill.objects.filter(patient=patient).order_by('-created_at').first()
    
    context = {
        'patient': patient,
        'latest_visit': latest_visit,
        'latest_vitals': latest_vitals,
        'bmi': bmi,
        'latest_prescription': latest_prescription,
        'latest_opd_visit': latest_opd_visit,
        'latest_lab_bill': latest_lab_bill,
        'active_nav': 'patient_list',
    }
    return render(request, "receptionist/patient_profile.html", context)


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
                        'height': form.cleaned_data.get('height') or None,
                        'temperature': form.cleaned_data['temperature'],
                        'heart_rate': form.cleaned_data['heart_rate'],
                        'pulse_rate': form.cleaned_data.get('pulse_rate') or None,
                        'blood_pressure': form.cleaned_data['blood_pressure'],
                        'spo2': form.cleaned_data['spo2'],
                        'respiratory_rate': form.cleaned_data.get('respiratory_rate') or None,
                        'bottle_feed': form.cleaned_data.get('bottle_feed') or None,
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
            vitals.height = form.cleaned_data.get('height') or None
            vitals.temperature = form.cleaned_data['temperature']
            vitals.heart_rate = form.cleaned_data['heart_rate']
            vitals.pulse_rate = form.cleaned_data.get('pulse_rate') or None
            vitals.blood_pressure = form.cleaned_data['blood_pressure']
            vitals.spo2 = form.cleaned_data['spo2']
            vitals.respiratory_rate = form.cleaned_data.get('respiratory_rate') or None
            vitals.bottle_feed = form.cleaned_data.get('bottle_feed') or None
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
        
    if visit and visit.visit_type == OPDVisit.VisitTypeChoices.FOLLOW_UP:
        from django.contrib import messages
        messages.error(request, "Receipts cannot be generated for Free Follow-up visits.")
        return redirect('receptionist:patient_list')
    
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
        from django.contrib import messages

        from django.utils import timezone
        from .models import Patient, OPDVisit, HospitalSettings
        
        patient = get_object_or_404(Patient, id=patient_id)
        payment_mode = request.POST.get('payment_mode')
        
        if not payment_mode or payment_mode not in ['CASH', 'UPI']:
            messages.error(request, "Invalid or missing Payment Mode.")
            return redirect('receptionist:patient_list')
            
        hospital = HospitalSettings.objects.first()
        if not hospital:
            hospital = HospitalSettings.objects.create(
                hospital_name="Vatsalya Shree Hospital",
                address="Near Shrinath Talkies, Main Road, Guna (M.P.)",
                phone_number="+91 7542 250000",
                email="contact@vatsalyashree.com",
                consultation_fee=350.00
            )
            
        visit_type_from_post = request.POST.get('visit_type')
        if visit_type_from_post == 'Follow-up':
            # Check if a Follow-up visit already exists for this patient
            if OPDVisit.objects.filter(patient=patient, visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP).exists():
                messages.error(request, f"A Follow-up visit has already been created for {patient.full_name}.")
                return redirect('receptionist:patient_list')
            visit_type = OPDVisit.VisitTypeChoices.FOLLOW_UP
        else:
            visit_type = determine_visit_type(patient, hospital)
        
        with transaction.atomic():
            # Create a new OPD visit
            visit = OPDVisit(
                patient=patient,
                visit_date=timezone.localdate(),
                visit_time=timezone.localtime().time().replace(second=0, microsecond=0),
                visit_type=visit_type,
                status=OPDVisit.StatusChoices.WAITING,
                payment_mode=payment_mode,
                created_by=request.user,
                updated_by=request.user
            )
            visit.save()
        
        messages.success(request, f"New OPD visit created successfully for {patient.full_name}!")
        if visit_type_from_post == 'Follow-up':
            return redirect('receptionist:patient_list')
        elif visit.visit_type == OPDVisit.VisitTypeChoices.NEW_VISIT:
            return redirect(f"{reverse('receptionist:opd_receipt', kwargs={'patient_id': patient.id})}?visit_id={visit.id}")
        else:
            return redirect(reverse('receptionist:vitals_entry_detail', kwargs={'patient_id': patient.id}))
        
    return redirect('receptionist:patient_list')


@receptionist_required
def received_lab_reports(request):
    from lab.models import LaboratoryCase, LaboratoryReport
    
    visit_id = request.GET.get('visit_id')
    if visit_id:
        from receptionist.models import OPDVisit
        from django.shortcuts import get_object_or_404
        
        visit = get_object_or_404(OPDVisit, id=visit_id)
        patient = visit.patient
        reports = LaboratoryReport.objects.filter(visit=visit, status='SENT').select_related('lab_test')
        
        context = {
            "active_nav": "received_lab_reports",
            "visit": visit,
            "patient": patient,
            "reports": reports,
            "show_visit_reports": True,
        }
        return render(request, "receptionist/received_lab_reports.html", context)
        
    # Main listing view: Fetch cases where at least one report has status 'SENT'
    cases = LaboratoryCase.objects.filter(
        reports__status='SENT'
    ).distinct().select_related('patient', 'visit').prefetch_related('reports__lab_test').order_by('-created_at')
    
    # Process properties
    for case in cases:
        case.test_count = case.reports.filter(status='SENT').count()
        case.report_date = case.visit.visit_date if case.visit else case.created_at.date()
        
    context = {
        'active_nav': 'received_lab_reports',
        'cases': cases,
        'show_visit_reports': False,
    }
    return render(request, "receptionist/received_lab_reports.html", context)


@receptionist_required
def ipd_registration(request):
    from .models import Patient, OPDVisit, IPDAdmission
    from django.shortcuts import redirect, render
    from django.contrib import messages
    import datetime
    from django.db import transaction
    
    patient_id = request.GET.get('patient_id') or request.POST.get('patient_id')
    visit_id = request.GET.get('visit_id') or request.POST.get('visit_id')
    
    patient = None
    visit = None
    
    if patient_id:
        patient = Patient.objects.filter(id=patient_id).first()
    if visit_id:
        visit = OPDVisit.objects.filter(id=visit_id).select_related('patient', 'handwritten_prescription__doctor').first()
        if visit and not patient:
            patient = visit.patient
            
    admitting_doctor = None
    if visit:
        if hasattr(visit, 'handwritten_prescription') and visit.handwritten_prescription and visit.handwritten_prescription.doctor:
            admitting_doctor = visit.handwritten_prescription.doctor
        else:
            admitting_doctor = visit.created_by
            
    if request.method == 'POST':
        ward_type = request.POST.get('ward_type')
        room_number = request.POST.get('room_number')
        bed_number = request.POST.get('bed_number')
        diagnosis = request.POST.get('diagnosis', '').strip()
        admission_date = request.POST.get('admission_date')
        admission_time = request.POST.get('admission_time')
        deposit_amount_str = request.POST.get('deposit_amount', '').strip()
        payment_mode = request.POST.get('payment_mode', 'Cash').strip() or 'Cash'

        # 1. Field Validation
        if not patient:
            messages.error(request, "Patient details are missing. Please select a valid patient.")
            return redirect('receptionist:ipd_patients')

        if not deposit_amount_str:
            messages.error(request, "Security Deposit Money is required.")
            context = {
                'active_nav': 'ipd_patients',
                'patient': patient,
                'visit': visit,
                'admitting_doctor': admitting_doctor,
            }
            return render(request, "receptionist/ipd_registration.html", context)

        try:
            deposit_amount = int(deposit_amount_str)
            if deposit_amount < 0:
                raise ValueError()
        except ValueError:
            messages.error(request, "Security Deposit Money must be a non-negative integer.")
            context = {
                'active_nav': 'ipd_patients',
                'patient': patient,
                'visit': visit,
                'admitting_doctor': admitting_doctor,
            }
            return render(request, "receptionist/ipd_registration.html", context)

        if not ward_type or not admission_date or not admission_time:
            messages.error(request, "Please fill in all required fields (Admission Date, Time, Ward Type).")
            context = {
                'active_nav': 'ipd_patients',
                'patient': patient,
                'visit': visit,
                'admitting_doctor': admitting_doctor,
            }
            return render(request, "receptionist/ipd_registration.html", context)

        if ward_type in ['Private Ward', 'Deluxe Ward'] and not room_number:
            messages.error(request, "Room Number is required for Private and Deluxe Wards.")
            context = {
                'active_nav': 'ipd_patients',
                'patient': patient,
                'visit': visit,
                'admitting_doctor': admitting_doctor,
            }
            return render(request, "receptionist/ipd_registration.html", context)

        if ward_type in ['PICU', 'NICU'] and not bed_number:
            messages.error(request, "Bed Number is required for PICU and NICU.")
            context = {
                'active_nav': 'ipd_patients',
                'patient': patient,
                'visit': visit,
                'admitting_doctor': admitting_doctor,
            }
            return render(request, "receptionist/ipd_registration.html", context)
        
        # 2. Duplicate Prevention
        existing_admission = IPDAdmission.objects.filter(visit=visit).first() if visit else None
        if existing_admission:
            messages.info(request, f"Patient {patient.full_name} is already admitted. Showing IPD Deposit Receipt.")
            return redirect('receptionist:ipd_deposit_receipt', admission_id=existing_admission.id)

        # 3. Save atomically and generate receipt
        year = datetime.date.today().year
        prefix = f"IPD-DEP-{year}-"
        
        try:
            with transaction.atomic():
                last_adm = IPDAdmission.objects.filter(receipt_number__startswith=prefix).order_by('-receipt_number').first()
                if last_adm and last_adm.receipt_number:
                    try:
                        last_seq = int(last_adm.receipt_number.split('-')[-1])
                        next_seq = last_seq + 1
                    except ValueError:
                        next_seq = 1
                else:
                    next_seq = 1
                receipt_no = f"{prefix}{next_seq:05d}"
                
                # Mark visit as Admitted
                if visit:
                    visit.status = OPDVisit.StatusChoices.ADMITTED
                    visit.save()
                    
                # Save IPD Admission
                admission = IPDAdmission.objects.create(
                    patient=patient,
                    visit=visit,
                    admission_date=admission_date,
                    admission_time=admission_time,
                    admitting_doctor=admitting_doctor,
                    ward_type=ward_type,
                    room_number=room_number if ward_type in ['Private Ward', 'Deluxe Ward'] else None,
                    bed_number=bed_number if ward_type in ['PICU', 'NICU'] else None,
                    diagnosis=diagnosis,
                    deposit_amount=deposit_amount,  # Manually entered Security Deposit
                    payment_mode=payment_mode,
                    receipt_number=receipt_no,
                    receipt_date=admission_date,
                    receipt_time=admission_time,
                    status='Admitted'
                )
        except Exception as e:
            messages.error(request, f"Failed to save IPD Admission: {str(e)}")
            context = {
                'active_nav': 'ipd_patients',
                'patient': patient,
                'visit': visit,
                'admitting_doctor': admitting_doctor,
            }
            return render(request, "receptionist/ipd_registration.html", context)
            
        messages.success(request, f"Patient {patient.full_name} admitted successfully. Deposit Receipt generated.")
        return redirect('receptionist:ipd_deposit_receipt', admission_id=admission.id)
        
    context = {
        'active_nav': 'ipd_patients',
        'patient': patient,
        'visit': visit,
        'admitting_doctor': admitting_doctor,
    }
    return render(request, "receptionist/ipd_registration.html", context)


@receptionist_required
def ipd_deposit_receipt(request, admission_id):
    from .models import IPDAdmission, HospitalSettings
    from django.shortcuts import get_object_or_404
    
    admission = get_object_or_404(IPDAdmission, id=admission_id)
    hospital = HospitalSettings.objects.first()
    
    context = {
        'admission': admission,
        'hospital': hospital,
        'received_by': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
    }
    return render(request, "receptionist/IPD_receipt.html", context)




@receptionist_required
def ipd_patients(request):
    status_filter = request.GET.get('status', 'recommended')
    if status_filter == 'discharged':
        target_status = OPDVisit.StatusChoices.DISCHARGED
    else:
        target_status = OPDVisit.StatusChoices.IPD_RECOMMENDED

    ipd_visits = OPDVisit.objects.filter(
        status=target_status
    ).select_related('patient', 'vitals').order_by('-updated_at')
    
    context = {
        'active_nav': 'ipd_patients',
        'ipd_visits': ipd_visits,
        'base_template': 'receptionist/base.html',
        'status_filter': status_filter,
    }
    return render(request, "doctor/ipd_patients.html", context)


@receptionist_required
def ipd_bill(request):
    from .models import IPDAdmission, IPDBill
    from django.contrib import messages
    from django.shortcuts import redirect, render

    admission_id = request.GET.get('admission_id')
    patient_id = request.GET.get('patient_id')

    admission = None
    if admission_id:
        admission = IPDAdmission.objects.filter(id=admission_id).select_related('patient', 'admitting_doctor', 'visit').first()
    elif patient_id:
        admission = IPDAdmission.objects.filter(patient_id=patient_id).select_related('patient', 'admitting_doctor', 'visit').order_by('-admission_date').first()

    if not admission:
        messages.error(request, "Error: Valid admission record not specified or found.")
        return redirect('receptionist:ready_for_billing')

    # Fetch saved database snapshot IPDBill header
    bill = IPDBill.objects.filter(admission=admission).select_related('patient', 'admission', 'admission__admitting_doctor').first()

    if not bill:
        messages.warning(request, "Bill has not been saved yet. Please click 'Save' on the billing page before generating the final bill.")
        return redirect('receptionist:ipd_billing_page', admission_id=admission.id)

    # Read items strictly from saved IPDBillItem rows in saved Display Order
    bill_items = bill.items.all().order_by('display_order', 'created_at')

    # Build charges_map from saved IPDBillItem database rows for template rendering
    charges_map = {}
    for item in bill_items:
        p_name = item.particular
        p_code = p_name.upper().replace(' ', '_')
        item_data = {
            'particular': item.particular,
            'unit': item.unit,
            'duration_display': item.duration or "-",
            'rate': float(item.rate),
            'quantity': float(item.quantity),
            'amount': float(item.amount)
        }
        charges_map[p_code] = item_data
        
        # Keyword mapping for template keys
        upper_p = p_name.upper()
        if 'REGISTRATION' in upper_p:
            charges_map['REGISTRATION'] = item_data
        elif 'OXYGEN' in upper_p:
            charges_map['OXYGEN'] = item_data
        elif 'PHOTOTHERAPY' in upper_p or 'PHOTO' in upper_p:
            charges_map['PHOTOTHERAPY'] = item_data
        elif 'NURSING' in upper_p:
            charges_map['NURSING'] = item_data
        elif 'WARMER' in upper_p:
            charges_map['WARMER'] = item_data
        elif 'BED' in upper_p:
            if 'PICU' in upper_p or 'NICU' in upper_p:
                charges_map['BED_PICU'] = item_data
            elif 'PRIVATE' in upper_p or 'DELUXE' in upper_p:
                charges_map['BED_PRIVATE'] = item_data
            else:
                charges_map['BED_GENERAL'] = item_data
        elif 'DOCTOR' in upper_p or 'DOC' in upper_p:
            charges_map['DOC_VISIT'] = item_data
        elif 'NEBULIZER' in upper_p:
            charges_map['NEBULIZER'] = item_data
        elif 'EMERGENCY' in upper_p:
            charges_map['EMERGENCY'] = item_data
        elif 'SERVICE' in upper_p:
            charges_map['SERVICE'] = item_data
        elif 'WASTE' in upper_p or 'BIOMEDICAL' in upper_p:
            charges_map['WASTE'] = item_data
        elif any(k in upper_p for k in ['HFNC', 'VENTILATOR', 'CPAP', 'EQUIPMENT', 'RBS']):
            charges_map['EQUIPMENT'] = item_data

    from django.utils import timezone
    context = {
        'active_nav': 'ipd_bill',
        'bill': bill,
        'bill_items': bill_items,
        'admission': bill.admission,
        'patient': bill.patient,
        'doctor': bill.admission.admitting_doctor,
        'charges_map': charges_map,
        'gross_total': bill.gross_total,
        'discount': bill.discount,
        'deposit_amount': bill.deposit_received,
        'net_payable': bill.net_amount,
        'balance_due': bill.balance_due,
        'abs_balance_due': abs(bill.balance_due),
        'prepared_by': bill.created_by.get_full_name() if (bill.created_by and hasattr(bill.created_by, 'get_full_name')) else 'Receptionist',
        'generated_at': bill.created_at or timezone.now(),
    }

    return render(request, "receptionist/ipd_bill.html", context)



@receptionist_required
def admitted_patients(request):
    from .models import IPDAdmission
    from django.db.models import Q
    from django.utils import timezone
    
    # Fetch only active admissions (exclude discharged)
    queryset = IPDAdmission.objects.filter(status='Admitted').select_related(
        'patient', 'visit', 'admitting_doctor'
    )
    
    # Filter by date cohort
    filter_val = request.GET.get('filter', 'all')
    today = timezone.localdate()
    if filter_val == 'today':
        queryset = queryset.filter(admission_date=today)
        
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(patient__full_name__icontains=search_query) |
            Q(patient__uhid__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(admitting_doctor__first_name__icontains=search_query) |
            Q(admitting_doctor__last_name__icontains=search_query) |
            Q(ward_type__icontains=search_query) |
            Q(room_number__icontains=search_query)
        )
        
    admissions = queryset.order_by('-admission_date', '-admission_time')
    
    # Calculate Days Admitted dynamically from local date
    for admission in admissions:
        diff_days = max(0, (today - admission.admission_date).days)
        if diff_days == 1:
            admission.days_admitted_display = "1 Day"
        else:
            admission.days_admitted_display = f"{diff_days} Days"
            
    context = {
        'active_nav': 'admitted_patients',
        'admissions': admissions,
        'filter_val': filter_val,
        'search_query': search_query,
    }
    return render(request, "receptionist/admitted_patients.html", context)


@receptionist_required
def view_admission(request, admission_id):
    from .models import IPDAdmission
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    
    admission = get_object_or_404(
        IPDAdmission.objects.select_related('patient', 'visit', 'admitting_doctor'),
        id=admission_id
    )
    
    today = timezone.localdate()
    diff_days = max(0, (today - admission.admission_date).days)
    if diff_days == 1:
        days_admitted = "1 Day"
    else:
        days_admitted = f"{diff_days} Days"
        
    context = {
        'active_nav': 'admitted_patients',
        'admission': admission,
        'days_admitted': days_admitted,
    }
    return render(request, "receptionist/view_admission.html", context)


@receptionist_required
def edit_admission(request, admission_id):
    from .models import IPDAdmission
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    
    admission = get_object_or_404(
        IPDAdmission.objects.select_related('patient', 'visit', 'admitting_doctor'),
        id=admission_id
    )
    
    if request.method == 'POST':
        ward_type = request.POST.get('ward_type')
        room_number = request.POST.get('room_number')
        bed_number = request.POST.get('bed_number')
        diagnosis = request.POST.get('diagnosis', '')
        admission_date = request.POST.get('admission_date')
        admission_time = request.POST.get('admission_time')
        
        # Save updated data
        admission.ward_type = ward_type
        admission.room_number = room_number if ward_type in ['Private Ward', 'Deluxe Ward'] else None
        admission.bed_number = bed_number if ward_type in ['General Ward 1', 'General Ward 2', 'PICU', 'NICU'] else None
        admission.diagnosis = diagnosis
        if admission_date:
            admission.admission_date = admission_date
        if admission_time:
            admission.admission_time = admission_time
            
        admission.save()
        messages.success(request, f"Admission details for {admission.patient.full_name} updated successfully.")
        return redirect('receptionist:admitted_patients')
        
    context = {
        'active_nav': 'admitted_patients',
        'admission': admission,
    }
    return render(request, "receptionist/edit_admission.html", context)


@receptionist_required
def ready_for_billing(request):
    from .models import IPDAdmission, IPDBill
    from django.db.models import Q
    from django.utils import timezone
    
    # Fetch only patients marked as 'Ready for Billing' who do NOT have a Final/Paid IPDBill
    queryset = IPDAdmission.objects.filter(status='Ready for Billing').exclude(
        ipd_bills__status__in=[IPDBill.StatusChoices.FINAL, IPDBill.StatusChoices.PAID]
    ).select_related(
        'patient', 'visit', 'admitting_doctor'
    )
    
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(patient__full_name__icontains=search_query) |
            Q(patient__uhid__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(admitting_doctor__first_name__icontains=search_query) |
            Q(admitting_doctor__last_name__icontains=search_query) |
            Q(ward_type__icontains=search_query) |
            Q(room_number__icontains=search_query)
        )
        
    admissions = queryset.order_by('-admission_date', '-admission_time')
    today = timezone.localdate()
    
    # Calculate Days Admitted dynamically from local date
    for admission in admissions:
        diff_days = max(0, (today - admission.admission_date).days)
        if diff_days == 1:
            admission.days_admitted_display = "1 Day"
        else:
            admission.days_admitted_display = f"{diff_days} Days"
            
    context = {
        'active_nav': 'ready_for_billing',
        'admissions': admissions,
        'search_query': search_query,
    }
    return render(request, "receptionist/ready_for_billing.html", context)


@receptionist_required
def ipd_billing_page(request, admission_id):
    from .models import IPDAdmission, IPDChargeMaster
    from lab.models import LaboratoryBill
    from django.utils import timezone
    from django.contrib import messages
    from django.http import JsonResponse
    from django.shortcuts import get_object_or_404, redirect, render

    admission = get_object_or_404(
        IPDAdmission.objects.select_related('patient', 'admitting_doctor', 'visit'),
        id=admission_id
    )
    patient = admission.patient
    
    # Calculate Days Admitted
    # If the patient is already discharged/closed, use the actual discharge date to calculate days
    if admission.status == 'Closed' and admission.discharge_date:
        days_admitted = max(1, (admission.discharge_date - admission.admission_date).days)
    else:
        today = timezone.localdate()
        days_admitted = max(1, (today - admission.admission_date).days)
    
    # Define daily rates
    WARD_RATES = {
        'Private Ward': 2000.00,
        'Deluxe Ward': 3500.00,
        'General Ward 1': 800.00,
        'General Ward 2': 800.00,
        'PICU': 3000.00,
        'NICU': 3000.00,
    }
    ward_rate = WARD_RATES.get(admission.ward_type, 1000.00)
    room_charges = float(ward_rate) * days_admitted
    
    service_charges = 200.00 * days_admitted
    nursing_charges = 300.00 * days_admitted
    biomedical_waste_charges = 100.00 * days_admitted
    
    # Calculate dynamic optional charges if selected during admission
    warmer_charges = 500.00 * days_admitted if admission.has_warmer else 0.00
    monitor_charges = 800.00 * days_admitted if admission.has_monitor else 0.00
    hfnc_charges = 1500.00 * days_admitted if admission.has_hfnc else 0.00
    ventilator_charges = 2500.00 * days_admitted if admission.has_ventilator else 0.00
    infusion_pump_charges = 300.00 * days_admitted if admission.has_infusion_pump else 0.00
    ac_charges = 500.00 * days_admitted if admission.has_ac else 0.00
    
    other_daily_charges = warmer_charges + monitor_charges + hfnc_charges + ventilator_charges + infusion_pump_charges + ac_charges
    
    # Fetch Laboratory and X-Ray charges
    lab_bills = LaboratoryBill.objects.filter(visit=admission.visit)
    total_lab_charges = 0.00
    total_xray_charges = 0.00
    
    for bill in lab_bills:
        xray_items = bill.items.filter(name__icontains="X-Ray")
        total_xray_charges += sum(float(item.price) for item in xray_items)
        
        other_items = bill.items.exclude(name__icontains="X-Ray")
        total_lab_charges += sum(float(item.price) for item in other_items)
        
    security_deposit = float(admission.deposit_amount)
    
    bill = None

    if request.method == "POST":
        from django.db import transaction
        action = request.POST.get('action') # 'save_draft', 'generate_final', or 'collect_payment'
        
        # Read optional editable fields with safe defaults
        days_admitted_val = request.POST.get('days_admitted')
        if days_admitted_val and str(days_admitted_val).strip() != '':
            try:
                days_admitted = max(1, int(days_admitted_val))
            except ValueError:
                days_admitted = 1
        else:
            days_admitted = 1

        # Re-calculate day-based charges using final days_admitted
        room_charges = float(ward_rate) * days_admitted
        service_charges = 200.00 * days_admitted
        nursing_charges = 300.00 * days_admitted
        biomedical_waste_charges = 100.00 * days_admitted
        warmer_charges = 500.00 * days_admitted if admission.has_warmer else 0.00
        monitor_charges = 800.00 * days_admitted if admission.has_monitor else 0.00
        hfnc_charges = 1500.00 * days_admitted if admission.has_hfnc else 0.00
        ventilator_charges = 2500.00 * days_admitted if admission.has_ventilator else 0.00
        infusion_pump_charges = 300.00 * days_admitted if admission.has_infusion_pump else 0.00
        ac_charges = 500.00 * days_admitted if admission.has_ac else 0.00
        other_daily_charges = warmer_charges + monitor_charges + hfnc_charges + ventilator_charges + infusion_pump_charges + ac_charges

        oxygen_hours = float(request.POST.get('oxygen_hours', 0) or 0)
        injection_charges = float(request.POST.get('injection_charges', 0) or 0)
        doctor_visit_charges = float(request.POST.get('doctor_visit_charges', 0) or 0)
        emergency_charges = float(request.POST.get('emergency_charges', 0) or 0)
        visiting_doctor_charges = float(request.POST.get('visiting_doctor_charges', 0) or 0)
        physiotherapy_charges = float(request.POST.get('physiotherapy_charges', 0) or 0)
        oxygen_charges = float(request.POST.get('oxygen_charges', 0) or 0)
        misc_charges = float(request.POST.get('misc_charges', 0) or 0)
        discount = float(request.POST.get('discount', 0) or 0)
        
        # Validation for negative inputs
        if oxygen_hours < 0 or oxygen_charges < 0:
            msg = "Validation Error: Oxygen Total Hours and Total Oxygen Charge must be 0 or greater."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('receptionist:ipd_billing_page', admission_id=admission.id)
        
        # Total Gross calculation
        gross_amount = (
            room_charges +
            service_charges +
            nursing_charges +
            biomedical_waste_charges +
            other_daily_charges +
            injection_charges +
            doctor_visit_charges +
            emergency_charges +
            visiting_doctor_charges +
            physiotherapy_charges +
            oxygen_charges +
            misc_charges +
            total_lab_charges +
            total_xray_charges
        )
        
        net_payable = max(0.00, gross_amount - security_deposit - discount)
        
        with transaction.atomic():
            if action == 'collect_payment':
                payment_mode = request.POST.get('payment_mode')
                payment_ref = ""
                
                # Validation: Mixed Payment check
                if payment_mode == 'Mixed Payment':
                    cash_amount = float(request.POST.get('mix_cash', 0) or 0)
                    upi_amount = float(request.POST.get('mix_upi', 0) or 0)
                    card_amount = float(request.POST.get('mix_card', 0) or 0)
                    bank_amount = float(request.POST.get('mix_bank', 0) or 0)
                    cheque_amount = float(request.POST.get('mix_cheque', 0) or 0)
                    
                    total_paid = cash_amount + upi_amount + card_amount + bank_amount + cheque_amount
                    
                    if cash_amount < 0 or upi_amount < 0 or card_amount < 0 or bank_amount < 0 or cheque_amount < 0:
                        messages.error(request, "Validation Error: Payment amounts cannot be negative.")
                        return redirect('receptionist:ipd_billing_page', admission_id=admission.id)
                    
                    if total_paid > net_payable:
                        messages.error(request, f"Validation Error: Total Mixed Payment paid (₹{total_paid:.2f}) cannot exceed Net Payable (₹{net_payable:.2f}).")
                        return redirect('receptionist:ipd_billing_page', admission_id=admission.id)
                        
                    if abs(total_paid - net_payable) > 0.01:
                        messages.error(request, f"Validation Error: Payment is incomplete. Total paid (₹{total_paid:.2f}) must exactly equal Net Payable (₹{net_payable:.2f}).")
                        return redirect('receptionist:ipd_billing_page', admission_id=admission.id)
                    
                    payment_ref = f"Mixed (Cash: {cash_amount}, UPI: {upi_amount}, Card: {card_amount}, Bank: {bank_amount}, Cheque: {cheque_amount})"
                else:
                    if payment_mode == 'UPI':
                        payment_ref = request.POST.get('upi_ref', '').strip()
                        if not payment_ref:
                            messages.error(request, "Validation Error: UPI Reference Number is required.")
                            return redirect('receptionist:ipd_billing_page', admission_id=admission.id)
                    elif payment_mode == 'Card':
                        payment_ref = request.POST.get('card_tx_id', '').strip()
                        if not payment_ref:
                            messages.error(request, "Validation Error: Card Transaction ID is required.")
                            return redirect('receptionist:ipd_billing_page', admission_id=admission.id)
                    elif payment_mode == 'Bank Transfer':
                        payment_ref = request.POST.get('bank_ref', '').strip()
                        if not payment_ref:
                            messages.error(request, "Validation Error: Bank Reference Number is required.")
                            return redirect('receptionist:ipd_billing_page', admission_id=admission.id)
                    elif payment_mode == 'Cheque':
                        payment_ref = request.POST.get('cheque_no', '').strip()
                        if not payment_ref:
                            messages.error(request, "Validation Error: Cheque Number is required.")
                            return redirect('receptionist:ipd_billing_page', admission_id=admission.id)
            
                # Update objects to final paid and discharge state
                discharge_date = timezone.localdate()
                discharge_time = timezone.localtime().time()
                
                # Close Admission
                admission.status = 'Closed'
                admission.discharge_date = discharge_date
                admission.discharge_time = discharge_time
                admission.save()
                
                # Close OPD Visit
                visit = admission.visit
                visit.status = OPDVisit.StatusChoices.DISCHARGED
                visit.save()
                
                messages.success(request, f"IPD Patient discharged successfully.")
                return redirect('receptionist:discharged_patients')
                
            else:
                if action in ['save_draft', 'save', 'finalize', 'generate_final']:
                    from .models import IPDBill, IPDBillItem
                    from .billing_rules_engine import IPDBillingRulesEngine

                    # 1. Retrieve existing IPDBill header or construct a new instance
                    bill_obj = IPDBill.objects.filter(admission=admission).first()

                    # Read-only security enforcement
                    if bill_obj and bill_obj.status in [IPDBill.StatusChoices.FINAL, IPDBill.StatusChoices.PAID]:
                        messages.warning(request, "Security Notification: This IPD Bill has already been Finalized/Paid and is Read-Only. Further edits or saves are blocked.")
                        return redirect('receptionist:ipd_billing_page', admission_id=admission.id)

                    if not bill_obj:
                        bill_obj = IPDBill(
                            bill_number=f"BILL-IPD-{admission.id.hex[:8].upper()}",
                            patient=admission.patient,
                            admission=admission,
                        )

                    # 2. Extract input values submitted from the form
                    ox_hrs = float(request.POST.get('oxygen_hours', 0) or 0)
                    ox_chg = float(request.POST.get('oxygen_charges', 0) or 0)
                    photo_hrs = float(request.POST.get('phototherapy_hours', 0) or 0)
                    doc_vsts = int(float(request.POST.get('total_doctor_visits', 0) or 0))
                    neb_uses = int(float(request.POST.get('total_nebulizer_uses', 0) or 0))
                    emg_chg = float(request.POST.get('emergency_charges', 0) or 0)
                    disc_val = float(request.POST.get('discount', 0) or 0)
                    selected_payment_mode = request.POST.get('payment_mode', '').strip()
                    if selected_payment_mode in ['Cash', 'UPI']:
                        admission.payment_mode = selected_payment_mode
                        admission.save(update_fields=['payment_mode'])
                    included_charge_codes = request.POST.getlist('included_charges')

                    # 3. Retrieve applicable charges for the admission ward
                    rules_data = IPDBillingRulesEngine.get_applicable_charges(admission)
                    applicable_charges = rules_data.get('applicable_charges', [])

                    calculated_items = []
                    gross_total = 0.00

                    for idx, chg_item in enumerate(applicable_charges):
                        p_name = chg_item.get('name', '')
                        p_code = chg_item.get('code', '')

                        # Skip unchecked charges if included_charges list was sent in POST
                        if 'included_charges' in request.POST and p_code not in included_charge_codes:
                            continue
                        u_type = chg_item.get('unit') or chg_item.get('charge_type') or ''
                        c_type = (chg_item.get('charge_type') or '').lower()
                        rate = float(chg_item.get('rate', 0))

                        duration_str = "-"
                        qty_num = 1.00
                        item_amt = 0.00

                        if "registration" in p_name.lower() or p_code == "REG":
                            duration_str = "One Time"
                            qty_num = 1.00
                            item_amt = rate * 1.00
                        elif "doctor" in p_name.lower() or p_code == "DOC_VISIT":
                            if "visit" in u_type.lower() or "visit" in c_type:
                                duration_str = f"{doc_vsts} Visits"
                                qty_num = float(doc_vsts)
                                item_amt = rate * qty_num
                            else:
                                duration_str = f"{days_admitted} Days"
                                qty_num = float(days_admitted)
                                item_amt = rate * qty_num
                        elif "oxygen" in p_name.lower() or p_code == "OXYGEN":
                            duration_str = f"{ox_hrs} Hours"
                            qty_num = 1.00
                            item_amt = ox_chg
                        elif "phototherapy" in p_name.lower() or "photo" in p_name.lower() or p_code == "PHYSIO":
                            duration_str = f"{photo_hrs} Hours"
                            qty_num = float(photo_hrs)
                            item_amt = rate * qty_num
                        elif "nebulizer" in p_name.lower() or "nebulizer" in p_code.lower():
                            if neb_uses > 0:
                                if rate > 0 and neb_uses <= 20:
                                    item_amt = rate * float(neb_uses)
                                    qty_num = float(neb_uses)
                                    duration_str = f"{neb_uses} Uses"
                                else:
                                    item_amt = float(neb_uses)
                                    rate = item_amt
                                    qty_num = 1.00
                                    duration_str = "Per Use / Charges"
                            else:
                                item_amt = 0.00
                                qty_num = 0.00
                                duration_str = "-"
                        elif "emergency" in p_name.lower() or "emergency" in p_code.lower():
                            if emg_chg > 0:
                                item_amt = emg_chg
                                rate = emg_chg
                                qty_num = 1.00
                                duration_str = "One Time"
                            else:
                                item_amt = rate
                                qty_num = 1.00
                                duration_str = "One Time"
                        elif "rbs" in p_name.lower() or p_code == "RBS":
                            duration_str = "One Test"
                            qty_num = 1.00
                            item_amt = rate * 1.00
                        else:
                            duration_str = f"{days_admitted} Days"
                            qty_num = float(days_admitted)
                            item_amt = rate * qty_num

                        gross_total += item_amt
                        calculated_items.append({
                            'particular': p_name,
                            'unit': u_type,
                            'duration': duration_str,
                            'rate': rate,
                            'quantity': qty_num,
                            'amount': item_amt,
                            'display_order': idx + 1
                        })

                    final_discount = min(disc_val, gross_total)
                    dep_received = float(admission.deposit_amount or 0)
                    net_amt = max(0.00, gross_total - final_discount)
                    bal_due = net_amt - dep_received

                    # 4. Save Header
                    bill_obj.gross_total = gross_total
                    bill_obj.discount = final_discount
                    bill_obj.deposit_received = dep_received
                    bill_obj.net_amount = net_amt
                    bill_obj.balance_due = bal_due

                    if action in ['finalize', 'generate_final']:
                        bill_obj.status = IPDBill.StatusChoices.FINAL
                        bill_obj.finalized_at = timezone.now()
                        if request.user.is_authenticated:
                            bill_obj.finalized_by = request.user
                        admission.status = 'Closed'
                        if not admission.discharge_date:
                            admission.discharge_date = timezone.localdate()
                        if not admission.discharge_time:
                            admission.discharge_time = timezone.localtime().time()
                        admission.save(update_fields=['status', 'discharge_date', 'discharge_time'])

                        if admission.visit:
                            admission.visit.status = OPDVisit.StatusChoices.DISCHARGED
                            admission.visit.save(update_fields=['status'])
                    else:
                        bill_obj.status = IPDBill.StatusChoices.DRAFT

                    if action in ['finalize', 'generate_final'] or bill_obj.status == IPDBill.StatusChoices.FINAL:
                        bill_obj.payment_status = IPDBill.PaymentStatusChoices.PAID
                    elif bal_due <= 0:
                        bill_obj.payment_status = IPDBill.PaymentStatusChoices.PAID
                    elif dep_received > 0:
                        bill_obj.payment_status = IPDBill.PaymentStatusChoices.PARTIAL
                    else:
                        bill_obj.payment_status = IPDBill.PaymentStatusChoices.PENDING

                    if selected_payment_mode in ['Cash', 'UPI']:
                        bill_obj.payment_mode = selected_payment_mode

                    if request.user.is_authenticated:
                        if not bill_obj.created_by:
                            bill_obj.created_by = request.user
                        bill_obj.updated_by = request.user

                    bill_obj.save()

                    # 5. Idempotent line item persistence (delete old items & bulk create new)
                    bill_obj.items.all().delete()

                    new_db_items = [
                        IPDBillItem(
                            bill=bill_obj,
                            particular=it['particular'],
                            unit=it['unit'],
                            duration=it['duration'],
                            rate=it['rate'],
                            quantity=it['quantity'],
                            amount=it['amount'],
                            display_order=it['display_order']
                        )
                        for it in calculated_items
                    ]
                    IPDBillItem.objects.bulk_create(new_db_items)

                    if action == 'generate_final':
                        messages.success(request, "Final IPD Bill generated successfully.")
                        return redirect(f"{reverse('receptionist:ipd_bill')}?admission_id={admission.id}")
                    elif action == 'finalize':
                        messages.success(request, "IPD Bill finalized successfully! The bill is now locked and read-only.")
                        return redirect('receptionist:ipd_billing_page', admission_id=admission.id)

                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'status': 'success', 'message': 'IPD Bill draft saved successfully.'})

                    messages.success(request, "IPD Bill saved successfully.")
                    return redirect('receptionist:ipd_billing_page', admission_id=admission.id)


            
    # GET details
    # Pre-populate fields from existing bill if exists
    if bill:
        injection_charges = float(getattr(bill, 'injection_charges', 0.00))
        doctor_visit_charges = float(getattr(bill, 'doctor_visit_charges', 0.00))
        emergency_charges = float(getattr(bill, 'emergency_charges', 0.00))
        visiting_doctor_charges = float(getattr(bill, 'visiting_doctor_charges', 0.00))
        physiotherapy_charges = float(getattr(bill, 'physiotherapy_charges', 0.00))
        oxygen_charges = float(getattr(bill, 'oxygen_charges', 0.00))
        misc_charges = float(getattr(bill, 'misc_charges', 0.00))
        discount = float(bill.discount)

        emg_item = bill.items.filter(particular__icontains='emergency').first()
        if emg_item:
            emergency_charges = float(emg_item.amount)

        neb_item = bill.items.filter(particular__icontains='nebulizer').first()
        total_nebulizer_uses = int(float(neb_item.quantity)) if neb_item else 0
    else:
        injection_charges = 0.00
        doctor_visit_charges = 0.00
        emergency_charges = 0.00
        visiting_doctor_charges = 0.00
        physiotherapy_charges = 0.00
        oxygen_charges = 0.00
        misc_charges = 0.00
        total_nebulizer_uses = 0
        discount = 0.00
        
    context = {
        'active_nav': 'ready_for_billing' if admission.status != 'Closed' else 'discharged_patients',
        'admission': admission,
        'patient': patient,
        'days_admitted': days_admitted,
        'ward_rate': ward_rate,
        'room_charges': room_charges,
        'service_charges': service_charges,
        'nursing_charges': nursing_charges,
        'biomedical_waste_charges': biomedical_waste_charges,
        
        # Equipment breakdown
        'has_warmer': admission.has_warmer,
        'has_monitor': admission.has_monitor,
        'has_hfnc': admission.has_hfnc,
        'has_ventilator': admission.has_ventilator,
        'has_infusion_pump': admission.has_infusion_pump,
        'has_ac': admission.has_ac,
        
        'warmer_charges': warmer_charges,
        'monitor_charges': monitor_charges,
        'hfnc_charges': hfnc_charges,
        'ventilator_charges': ventilator_charges,
        'infusion_pump_charges': infusion_pump_charges,
        'ac_charges': ac_charges,
        'other_daily_charges': other_daily_charges,
        
        # Integrations
        'total_lab_charges': total_lab_charges,
        'total_xray_charges': total_xray_charges,
        'security_deposit': security_deposit,
        
        # Optional editable
        'injection_charges': injection_charges,
        'doctor_visit_charges': doctor_visit_charges,
        'emergency_charges': emergency_charges,
        'total_nebulizer_uses': total_nebulizer_uses,
        'visiting_doctor_charges': visiting_doctor_charges,
        'physiotherapy_charges': physiotherapy_charges,
        'oxygen_charges': oxygen_charges,
        'misc_charges': misc_charges,
        
        # Totals
        'discount': discount,
        'payment_mode': (bill.payment_mode if (bill and bill.payment_mode) else admission.payment_mode) or 'Cash',
        'bill': bill,
        'charge_masters': IPDChargeMaster.objects.all(),
    }

    # Build exact 14 final billing particulars mapped from IPDChargeMaster & assigned ward/bed
    charges_dict = {c.code: c for c in context['charge_masters']}
    ward_code_map = {
        'Private Ward': 'WARD_PRI',
        'Deluxe Ward': 'WARD_DEL',
        'General Ward 1': 'WARD_GEN',
        'General Ward 2': 'WARD_GEN',
        'PICU': 'WARD_PICU',
        'NICU': 'WARD_NICU',
    }
    bed_code = ward_code_map.get(admission.ward_type, 'WARD_GEN')
    bed_charge_obj = charges_dict.get(bed_code)

    # Determine dynamic Doctor Visit Rate based on admitted Ward type
    ward_type_str = str(admission.ward_type or '')
    doc_visit_rate = 400.00 if 'General' in ward_type_str else 500.00

    particular_specs = [
        ('Registration', 'REG', 'One Time'),
        ('Oxygen Charges', 'OXYGEN', 'Per Hour'),
        ('Phototherapy', 'PHYSIO', 'Per Hour'),
        ('Nursing Charges', 'NURSING', 'Per Day'),
        ('Warmer Charges', 'WARMER', 'Per Day'),
        (f'Bed Charges ({admission.ward_type})', bed_code, 'Per Day'),
        ('Doctor Visit Fees', 'DOC_VISIT', 'Per Visit'),
        ('Nebulizer Charges', 'NEBULIZER', 'Per Use'),
        ('Emergency Charges', 'EMERGENCY', 'One Time'),
        ('Service Charges', 'SERVICE', 'Per Day'),
        ('Biomedical Waste Charge', 'BMW', 'Per Day'),
        ('HFNC Charges', 'HFNC', 'Per Day'),
        ('Ventilator Charges', 'VENTILATOR', 'Per Day'),
        ('RBS Charges', 'RBS', 'Per Test'),
    ]

    final_particulars = []
    for title, code, default_type in particular_specs:
        obj = charges_dict.get(code)
        rate = float(obj.amount) if obj else 0.00
        c_type = obj.charge_type if obj else default_type
        if code == bed_code and bed_charge_obj:
            rate = float(bed_charge_obj.amount)
            c_type = bed_charge_obj.charge_type
        elif code == bed_code:
            rate = float(ward_rate)
        elif code == 'DOC_VISIT':
            rate = doc_visit_rate
            c_type = 'Per Visit'
        
        final_particulars.append({
            'name': title,
            'code': code,
            'rate': rate,
            'charge_type': c_type,
        })

    from .models import IPDBill
    saved_bill = IPDBill.objects.filter(admission=admission).select_related('patient', 'admission', 'created_by', 'updated_by', 'finalized_by').first()
    bill_history = IPDBill.objects.filter(patient=admission.patient).select_related('patient', 'admission', 'created_by', 'finalized_by').order_by('-created_at')
    is_read_only = bool(saved_bill and saved_bill.status in [IPDBill.StatusChoices.FINAL, IPDBill.StatusChoices.PAID])

    context['saved_bill'] = saved_bill
    context['bill_history'] = bill_history
    context['is_read_only'] = is_read_only

    from .billing_rules_engine import IPDBillingRulesEngine
    context['rules_engine_data'] = IPDBillingRulesEngine.get_applicable_charges(admission)
    context['final_particulars'] = final_particulars
    return render(request, "receptionist/ipd_billing_page.html", context)


@receptionist_required
def discharged_patients(request):
    from .models import IPDAdmission
    from django.db.models import Q
    from django.utils import timezone
    
    today = timezone.localdate()
    
    # Base queryset for all discharged patients according to HMS discharge workflow
    base_qs = IPDAdmission.objects.filter(
        Q(status='Closed') | Q(discharge_date__isnull=False)
    ).select_related(
        'patient', 'visit', 'admitting_doctor'
    ).prefetch_related('ipd_bills')
    
    # Dynamic Counters
    total_discharged_count = base_qs.count()
    today_discharges_count = base_qs.filter(discharge_date=today).count()
    
    queryset = base_qs
    
    # Cohort filtering
    cohort = request.GET.get('cohort', 'all')
    if cohort == 'today':
        queryset = queryset.filter(discharge_date=today)
        
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(patient__full_name__icontains=search_query) |
            Q(patient__uhid__icontains=search_query) |
            Q(ipd_bills__bill_number__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(admitting_doctor__first_name__icontains=search_query) |
            Q(admitting_doctor__last_name__icontains=search_query)
        )
        
    admissions = queryset.distinct().order_by('-discharge_date', '-discharge_time')
    
    context = {
        'active_nav': 'discharged_patients',
        'admissions': admissions,
        'cohort': cohort,
        'search_query': search_query,
        'total_discharged_count': total_discharged_count,
        'today_discharges_count': today_discharges_count,
    }
    return render(request, "receptionist/discharged_patients.html", context)


@receptionist_required
def print_ipd_bill(request, bill_id):
    from .models import IPDAdmission, HospitalSettings, IPDBill
    bill = IPDBill.objects.filter(id=bill_id).first()
    admission = bill.admission if bill else (IPDAdmission.objects.filter(id=bill_id).first() or IPDAdmission.objects.first())
    if not bill and admission:
        bill = IPDBill.objects.filter(admission=admission).first()
    hospital = HospitalSettings.objects.first()
    days_admitted = max(1, (admission.discharge_date - admission.admission_date).days) if (admission and admission.discharge_date) else 1

    bill_items = bill.items.all().order_by('display_order', 'created_at') if bill else []
    charges_map = {}
    for item in bill_items:
        p_name = item.particular
        p_code = p_name.upper().replace(' ', '_')
        item_data = {
            'particular': item.particular,
            'unit': item.unit,
            'duration_display': item.duration or "-",
            'rate': float(item.rate),
            'quantity': float(item.quantity),
            'amount': float(item.amount)
        }
        charges_map[p_code] = item_data
        upper_p = p_name.upper()
        if 'REGISTRATION' in upper_p: charges_map['REGISTRATION'] = item_data
        elif 'OXYGEN' in upper_p: charges_map['OXYGEN'] = item_data
        elif 'PHOTOTHERAPY' in upper_p or 'PHOTO' in upper_p: charges_map['PHOTOTHERAPY'] = item_data
        elif 'NURSING' in upper_p: charges_map['NURSING'] = item_data
        elif 'WARMER' in upper_p: charges_map['WARMER'] = item_data
        elif 'BED' in upper_p:
            if 'PICU' in upper_p or 'NICU' in upper_p: charges_map['BED_PICU'] = item_data
            elif 'PRIVATE' in upper_p or 'DELUXE' in upper_p: charges_map['BED_PRIVATE'] = item_data
            else: charges_map['BED_GENERAL'] = item_data
        elif 'DOCTOR' in upper_p or 'DOC' in upper_p: charges_map['DOC_VISIT'] = item_data
        elif 'NEBULIZER' in upper_p: charges_map['NEBULIZER'] = item_data
        elif 'EMERGENCY' in upper_p: charges_map['EMERGENCY'] = item_data
        elif 'SERVICE' in upper_p: charges_map['SERVICE'] = item_data
        elif 'WASTE' in upper_p or 'BIOMEDICAL' in upper_p: charges_map['WASTE'] = item_data

    context = {
        'bill': bill,
        'bill_items': bill_items,
        'charges_map': charges_map,
        'admission': admission,
        'patient': admission.patient if admission else None,
        'doctor': admission.admitting_doctor if admission else None,
        'hospital': hospital,
        'days_admitted': days_admitted,
    }
    return render(request, "receptionist/print_ipd_bill.html", context)


@receptionist_required
def ipd_dashboard(request):
    from .models import IPDAdmission
    from django.db.models import Q
    from django.utils import timezone
    import datetime

    today = timezone.localdate()
    
    # Date filters for Analytics
    filter_type = request.GET.get('filter', 'all_time')
    
    start_date = None
    if filter_type == 'today':
        start_date = today
    elif filter_type == 'this_week':
        start_date = today - datetime.timedelta(days=7)
    elif filter_type == 'this_month':
        start_date = today - datetime.timedelta(days=30)
        
    admissions_qs = IPDAdmission.objects.all()
    discharges_qs = IPDAdmission.objects.filter(status='Closed')
    
    if start_date:
        admissions_qs = admissions_qs.filter(admission_date__gte=start_date)
        discharges_qs = discharges_qs.filter(discharge_date__gte=start_date)
        
    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        admissions_qs = admissions_qs.filter(
            Q(patient__full_name__icontains=search_query) |
            Q(patient__uhid__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(admitting_doctor__first_name__icontains=search_query) |
            Q(admitting_doctor__last_name__icontains=search_query) |
            Q(ward_type__icontains=search_query)
        )
        discharges_qs = discharges_qs.filter(
            Q(patient__full_name__icontains=search_query) |
            Q(patient__uhid__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(admitting_doctor__first_name__icontains=search_query) |
            Q(admitting_doctor__last_name__icontains=search_query) |
            Q(ward_type__icontains=search_query)
        )

    # Active Admissions (Currently Admitted)
    active_admissions = IPDAdmission.objects.filter(status__in=['Admitted', 'Ready for Billing']).select_related('patient', 'admitting_doctor')
    
    # Bed Capacities
    WARD_CAPACITIES = {
        'General Ward 1': 20,
        'General Ward 2': 20,
        'Private Ward': 10,
        'Deluxe Ward': 5,
        'PICU': 5,
        'NICU': 5,
    }
    total_capacity = sum(WARD_CAPACITIES.values())
    
    # Count occupancy per ward
    ward_occupancy = {}
    total_occupied_beds = 0
    for ward, cap in WARD_CAPACITIES.items():
        occ = active_admissions.filter(ward_type=ward).count()
        total_occupied_beds += occ
        avail = cap - occ
        pct = (occ / cap) * 100 if cap > 0 else 0
        ward_occupancy[ward] = {
            'name': ward,
            'capacity': cap,
            'occupied': occ,
            'available': avail,
            'percent': pct,
        }
        
    total_available_beds = total_capacity - total_occupied_beds
    occupancy_percent = (total_occupied_beds / total_capacity) * 100 if total_capacity > 0 else 0
    
    # Room status for Private Ward (Rooms 101 to 110)
    private_rooms = []
    private_admissions = active_admissions.filter(ward_type='Private Ward')
    for r_num in range(101, 111):
        adm = private_admissions.filter(room_number=str(r_num)).first()
        private_rooms.append({
            'number': r_num,
            'status': 'Occupied' if adm else 'Vacant',
            'patient_name': adm.patient.full_name if adm else '-',
            'admission_date': adm.admission_date if adm else '-',
        })
        
    # Room status for Deluxe Ward (Rooms 201 to 205)
    deluxe_rooms = []
    deluxe_admissions = active_admissions.filter(ward_type='Deluxe Ward')
    for r_num in range(201, 206):
        adm = deluxe_admissions.filter(room_number=str(r_num)).first()
        deluxe_rooms.append({
            'number': r_num,
            'status': 'Occupied' if adm else 'Vacant',
            'patient_name': adm.patient.full_name if adm else '-',
            'admission_date': adm.admission_date if adm else '-',
        })
        
    # PICU Beds status (Beds 1 to 5)
    picu_beds = []
    picu_admissions = active_admissions.filter(ward_type='PICU')
    for b_num in range(1, 6):
        adm = picu_admissions.filter(
            Q(bed_number=str(b_num)) | Q(bed_number=f"Bed {b_num}") | Q(bed_number=f"Bed {b_num:02d}")
        ).first()
        picu_beds.append({
            'number': f"Bed {b_num}",
            'status': 'Occupied' if adm else 'Vacant',
            'patient_name': adm.patient.full_name if adm else '-',
            'admission_date': adm.admission_date if adm else '-',
        })
        
    # NICU Beds status (Beds 1 to 5)
    nicu_beds = []
    nicu_admissions = active_admissions.filter(ward_type='NICU')
    for b_num in range(1, 6):
        adm = nicu_admissions.filter(
            Q(bed_number=str(b_num)) | Q(bed_number=f"Bed {b_num}") | Q(bed_number=f"Bed {b_num:02d}")
        ).first()
        nicu_beds.append({
            'number': f"Bed {b_num}",
            'status': 'Occupied' if adm else 'Vacant',
            'patient_name': adm.patient.full_name if adm else '-',
            'admission_date': adm.admission_date if adm else '-',
        })
        
    # Recent Admissions (latest 5)
    recent_admissions = IPDAdmission.objects.all().select_related('patient', 'admitting_doctor').order_by('-admission_date', '-admission_time')[:5]
    
    # Recent Discharges (latest 5)
    recent_discharges = IPDAdmission.objects.filter(status='Closed').select_related('patient', 'admitting_doctor').prefetch_related('ipd_bills').order_by('-discharge_date', '-discharge_time')[:5]
    
    # Analytics / Reports Calculations
    closed_admissions = IPDAdmission.objects.filter(status='Closed')
    total_admissions_count = admissions_qs.count()
    total_discharges_count = discharges_qs.count()
    
    # Calculate stay durations (min 1 day)
    stay_durations = []
    for adm in closed_admissions:
        if adm.discharge_date and adm.admission_date:
            duration = max(1, (adm.discharge_date - adm.admission_date).days)
            stay_durations.append(duration)
            
    avg_stay = sum(stay_durations) / len(stay_durations) if stay_durations else 0.0
    longest_stay = max(stay_durations) if stay_durations else 0
    
    # Top Summary Counts
    total_admissions = IPDAdmission.objects.count()
    currently_admitted = active_admissions.count()
    today_admissions = IPDAdmission.objects.filter(admission_date=today).count()
    today_discharges = IPDAdmission.objects.filter(status='Closed', discharge_date=today).count()
    
    context = {
        'active_nav': 'ipd_dashboard',
        
        # Summary counts
        'total_admissions': total_admissions,
        'currently_admitted': currently_admitted,
        'today_admissions': today_admissions,
        'today_discharges': today_discharges,
        
        'total_capacity': total_capacity,
        'total_occupied_beds': total_occupied_beds,
        'total_available_beds': total_available_beds,
        'occupancy_percent': occupancy_percent,
        
        # Ward occupancy detail
        'ward_occupancy': ward_occupancy,
        'private_rooms': private_rooms,
        'deluxe_rooms': deluxe_rooms,
        'picu_beds': picu_beds,
        'nicu_beds': nicu_beds,
        
        # Lists
        'recent_admissions': recent_admissions,
        'recent_discharges': recent_discharges,
        
        # Search & Filter
        'cohort': filter_type,
        'search_query': search_query,
        
        # Reports / Analytics
        'total_admissions_count': total_admissions_count,
        'total_discharges_count': total_discharges_count,
        'avg_stay': avg_stay,
        'longest_stay': longest_stay,
        'current_occupancy': currently_admitted,
    }
    
    return render(request, "receptionist/ipd_dashboard.html", context)


