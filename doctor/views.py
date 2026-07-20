import base64
import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from doctor.models import Prescription
from receptionist.models import OPDVisit, Patient, HospitalSettings
from lab.models import LaboratoryRequest

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    today = timezone.localdate()
    
    # Parse and validate selected date
    date_str = request.GET.get('date')
    selected_date = today
    if date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Calculate metric card counts
    waiting_count = OPDVisit.objects.filter(
        visit_date=selected_date,
        status=OPDVisit.StatusChoices.READY_FOR_DOCTOR,
        vitals__isnull=False
    ).count()
    completed_count = OPDVisit.objects.filter(
        visit_date=selected_date,
        status__in=[OPDVisit.StatusChoices.COMPLETED, OPDVisit.StatusChoices.IPD_RECOMMENDED]
    ).count()
    total_appointments = OPDVisit.objects.filter(
        visit_date=selected_date
    ).exclude(status=OPDVisit.StatusChoices.CANCELLED).count()
    
    # Fetch consultation fee and calculate collection
    hospital = HospitalSettings.objects.first()
    consultation_fee = hospital.consultation_fee if hospital else 200.00
    collection_amount = total_appointments * consultation_fee
    collection_str = f"₹{collection_amount:,.0f}"
    
    context = {
        "active_nav": "dashboard",
        "waiting_count": waiting_count,
        "completed_count": completed_count,
        "total_appointments": total_appointments,
        "collection_str": collection_str,
        "selected_date": selected_date,
        "today": today,
    }
    return render(request, "doctor/dashboard.html", context)


@login_required
def queue(request):
    today = timezone.localdate()
    from django.db.models import Q
    today_visits = OPDVisit.objects.filter(
        Q(visit_date=today) & (
            Q(visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP) |
            (
                Q(status__in=[
                    OPDVisit.StatusChoices.READY_FOR_DOCTOR,
                    OPDVisit.StatusChoices.PENDING_LAB,
                    OPDVisit.StatusChoices.COMPLETED,
                    OPDVisit.StatusChoices.IPD_RECOMMENDED
                ]) & Q(vitals__isnull=False)
            )
        )
    ).select_related('patient', 'handwritten_prescription').order_by('visit_time')
    
    # Get active LaboratoryRequest IDs for today
    lab_request_ids = set(
        LaboratoryRequest.objects.filter(
            visit_date=today,
            status=OPDVisit.StatusChoices.PENDING_LAB
        ).values_list('id', flat=True)
    )
    
    context = {
        "active_nav": "queue",
        "today_visits": today_visits,
        "lab_request_ids": lab_request_ids,
        "today": today,
    }
    return render(request, "doctor/queue.html", context)


@login_required
def patient_search(request):
    from django.db.models import Subquery, OuterRef, Q
    from receptionist.models import Patient, OPDVisit

    query = request.GET.get('q', '').strip()
    patient_type = request.GET.get('patient_type', 'all')

    patients = Patient.objects.all()

    # Apply search filter
    if query:
        patients = patients.filter(
            Q(uhid__icontains=query) |
            Q(full_name__icontains=query) |
            Q(mobile_number__icontains=query) |
            Q(father_name__icontains=query)
        )

    # Annotate latest visit details
    latest_visit_date = OPDVisit.objects.filter(
        patient=OuterRef('pk')
    ).order_by('-visit_date', '-visit_time').values('visit_date')[:1]

    latest_visit_type = OPDVisit.objects.filter(
        patient=OuterRef('pk')
    ).order_by('-visit_date', '-visit_time').values('visit_type')[:1]

    patients = patients.annotate(
        last_visit_date=Subquery(latest_visit_date),
        latest_visit_type=Subquery(latest_visit_type)
    ).order_by('full_name')

    # Apply patient type filter
    if patient_type == 'new':
        patients = patients.filter(latest_visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT)
    elif patient_type == 'followup':
        patients = patients.filter(latest_visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP)

    context = {
        "active_nav": "patient_search",
        "patients": patients,
        "query": query,
        "patient_type": patient_type
    }
    return render(request, "doctor/patient_search.html", context)


@login_required
def patient_summary(request):
    visit_id = request.GET.get('visit_id')
    patient_id = request.GET.get('patient_id')
    
    if not visit_id and not patient_id:
        return redirect('doctor:dashboard')
        
    from receptionist.models import Patient
    
    if visit_id:
        visit = get_object_or_404(OPDVisit.objects.select_related('patient', 'vitals'), id=visit_id)
        patient = visit.patient
    else:
        patient = get_object_or_404(Patient, id=patient_id)
        visit = OPDVisit.objects.filter(patient=patient).select_related('vitals').order_by('-visit_date', '-visit_time').first()
        if not visit:
            return redirect('doctor:dashboard')
            
    vitals = getattr(visit, 'vitals', None)
    
    # Calculate Last Visit Date from history (excluding current visit)
    previous_visits = OPDVisit.objects.filter(patient=patient).exclude(id=visit.id).order_by('-visit_date', '-visit_time')
    last_visit = previous_visits.first()
    last_visit_date = last_visit.visit_date if last_visit else None
    
    # Generate initials for avatar
    names = patient.full_name.split()
    avatar_initials = "".join([n[0].upper() for n in names[:2]]) if names else "P"
    
    # Get complete history for the patient
    consultations = OPDVisit.objects.filter(patient=patient).select_related('vitals').order_by('-visit_date', '-visit_time')
    
    # Fetch existing prescription and strokes
    prescription = Prescription.objects.filter(visit=visit).first()
    saved_strokes_json = "[]"
    if prescription and prescription.canvas_data:
        saved_strokes_json = json.dumps(prescription.canvas_data)
    
    context = {
        "active_nav": "patient_search",
        "visit": visit,
        "patient": patient,
        "vitals": vitals,
        "last_visit_date": last_visit_date,
        "consultations": consultations,
        "avatar_initials": avatar_initials,
        "saved_strokes_json": saved_strokes_json,
        "prescription": prescription,
    }
    return render(request, "doctor/patient_summary.html", context)


@login_required
def prescription(request):
    return render(request, "doctor/prescription.html", {"active_nav": "queue"})


@login_required
def prescription_preview(request):
    visit_id = request.GET.get('visit_id')
    patient_id = request.GET.get('patient_id')
    saved_image_url = None
    
    if visit_id:
        prescription = Prescription.objects.filter(visit_id=visit_id).first()
    elif patient_id:
        prescription = Prescription.objects.filter(patient_id=patient_id).order_by('-created_at').first()
    else:
        prescription = None
        
    if prescription and prescription.image:
        saved_image_url = prescription.image.url
        
    return render(request, "doctor/prescription_preview.html", {
        "active_nav": "queue",
        "saved_image_url": saved_image_url,
        "visit_id": visit_id,
        "patient_id": patient_id,
    })


@login_required
def prescription_print(request):
    visit_id = request.GET.get('visit_id')
    patient_id = request.GET.get('patient_id')
    from_module = request.GET.get('from', 'doctor')
    saved_image_url = None

    if visit_id:
        prescription = Prescription.objects.filter(visit_id=visit_id).first()
    elif patient_id:
        prescription = Prescription.objects.filter(patient_id=patient_id).order_by('-created_at').first()
    else:
        prescription = None

    if prescription and prescription.image:
        saved_image_url = prescription.image.url

    # Build back_url server-side — no template logic needed
    if from_module == 'receptionist' and patient_id:
        back_url = reverse('receptionist:patient_summary_detail', args=[patient_id])
    elif visit_id and patient_id:
        back_url = f"{reverse('doctor:patient_summary')}?visit_id={visit_id}&patient_id={patient_id}"
    elif patient_id:
        back_url = f"{reverse('doctor:patient_summary')}?patient_id={patient_id}"
    else:
        back_url = reverse('doctor:queue')

    return render(request, "doctor/prescription_print.html", {
        "active_nav": "queue",
        "saved_image_url": saved_image_url,
        "visit_id": visit_id,
        "patient_id": patient_id,
        "back_url": back_url,
    })


@login_required
def previous_history(request):
    return render(request, "doctor/previous_history.html", {"active_nav": "queue"})


@login_required
def profile(request):
    return render(request, "doctor/profile.html", {"active_nav": "profile"})


@login_required
def report_list(request):
    from receptionist.models import OPDVisit
    from lab.models import LaboratoryCase, LaboratoryReport, LaboratoryRequest
    from django.db import models
    
    visit_id = request.GET.get('visit_id')
    if visit_id:
        try:
            visit = OPDVisit.objects.get(id=visit_id)
            if visit.status in [OPDVisit.StatusChoices.READY_FOR_DOCTOR, OPDVisit.StatusChoices.COMPLETED, OPDVisit.StatusChoices.IN_CONSULTATION]:
                # Create/get LaboratoryRequest (linked to patient & visit since it's a proxy of OPDVisit)
                lab_req, created = LaboratoryRequest.objects.get_or_create(id=visit.id)
                lab_req.status = OPDVisit.StatusChoices.PENDING_LAB
                lab_req.save()
        except OPDVisit.DoesNotExist:
            pass
            
    # Fetch active visits that are requested for lab (status = PENDING_LAB or has a lab case)
    # and visit status is NOT Completed or Cancelled.
    requested_visits = OPDVisit.objects.exclude(
        status__in=[OPDVisit.StatusChoices.COMPLETED, OPDVisit.StatusChoices.CANCELLED]
    ).filter(
        models.Q(status=OPDVisit.StatusChoices.PENDING_LAB) | models.Q(laboratory_case__isnull=False)
    ).distinct().select_related('patient').prefetch_related('laboratory_case__reports__lab_test').order_by('-visit_date', '-visit_time')
    
    requested_patients = []
    for visit in requested_visits:
        # Determine status
        case_status = "Pending"
        status_class = "bg-warning text-dark"
        
        # Check if case and reports exist
        has_case = hasattr(visit, 'laboratory_case')
        reports = visit.laboratory_case.reports.all() if has_case else []
        
        if has_case and reports:
            # If all reports are SENT, it's Completed
            if all(r.status == 'SENT' for r in reports):
                case_status = "Completed"
                status_class = "bg-success text-white"
            # If any report is IN_PROGRESS or COMPLETED, it's In Progress
            elif any(r.status in ['IN_PROGRESS', 'COMPLETED'] for r in reports):
                case_status = "In Progress"
                status_class = "bg-info text-white"
            else:
                case_status = "Pending"
                status_class = "bg-warning text-dark"
        
        # Format requested tests name
        if has_case and reports:
            requested_tests = ", ".join([r.lab_test.name for r in reports])
        else:
            requested_tests = "Lab Investigation"
            
        requested_patients.append({
            'visit': visit,
            'patient': visit.patient,
            'requested_tests': requested_tests,
            'status': case_status,
            'status_class': status_class,
            'requested_date': visit.visit_date,
        })
        
    # Fetch cases where at least one report has status 'SENT'
    received_cases = LaboratoryCase.objects.filter(
        reports__status='SENT'
    ).distinct().select_related('patient', 'visit').prefetch_related('reports__lab_test').order_by('-created_at')
    
    received_patients = []
    for case in received_cases:
        received_patients.append({
            'case': case,
            'patient': case.patient,
            'visit': case.visit,
            'total_reports': case.reports.filter(status='SENT').count(),
            'report_date': case.visit.visit_date if case.visit else case.created_at.date(),
        })
        
    return render(request, "doctor/report_list.html", {
        "active_nav": "report_list",
        "requested_patients": requested_patients,
        "requested_count": len(requested_patients),
        "received_patients": received_patients,
        "received_count": len(received_patients),
    })


@login_required
def report_view(request):
    from receptionist.models import OPDVisit
    from lab.models import LaboratoryReport
    
    visit_id = request.GET.get('visit_id')
    visit = get_object_or_404(OPDVisit, id=visit_id)
    patient = visit.patient
    
    # Fetch all reports for this visit
    reports = LaboratoryReport.objects.filter(visit=visit).select_related('lab_test')
    
    context = {
        "active_nav": "report_list",
        "visit": visit,
        "patient": patient,
        "reports": reports,
    }
    return render(request, "doctor/report_view.html", context)


@login_required
@require_POST
def save_prescription(request):
    """Save or update the handwritten prescription image for an OPD visit."""
    try:
        data = json.loads(request.body)
        visit_id = data.get('visit_id')
        patient_id = data.get('patient_id')
        image_data = data.get('image_data', '')
        canvas_data = data.get('canvas_data', None)

        if not visit_id or not patient_id or not image_data:
            return JsonResponse({'status': 'error', 'message': 'Missing required fields.'}, status=400)

        # Validate the base64 data URL format
        if not image_data.startswith('data:image/'):
            return JsonResponse({'status': 'error', 'message': 'Invalid image data format.'}, status=400)

        # Decode the base64 image
        header, encoded = image_data.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        image_file = ContentFile(image_bytes, name='prescription.png')

        visit = get_object_or_404(OPDVisit, id=visit_id)
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Get Vitals
        vitals = getattr(visit, 'vitals', None)
        
        # Get Hospital Settings
        hospital = HospitalSettings.objects.first()
        hospital_info = {
            'hospital_name': hospital.hospital_name if hospital else "VATSALYA SHREE HOSPITAL",
            'address': hospital.address if hospital else "Near Shrinath Talkies, Main Road, Guna (M.P.)",
            'phone_number': hospital.phone_number if hospital else "+91 7542 250000",
            'email': hospital.email if hospital else "contact@vatsalyashree.com",
            'logo_url': hospital.hospital_logo.url if hospital and hospital.hospital_logo else "/static/images/vatsalya_logo.png"
        }
        
        # Build snapshot_data to freeze all patient/visit/vitals/doctor details
        snapshot = {
            'patient': {
                'full_name': patient.full_name,
                'age': patient.age,
                'gender': patient.gender,
                'mobile_number': patient.mobile_number,
                'address': patient.address,
                'uhid': patient.uhid,
            },
            'visit': {
                'opd_number': visit.opd_number,
                'visit_date': visit.visit_date.strftime('%Y-%m-%d') if visit.visit_date else '',
                'visit_time': visit.visit_time.strftime('%H:%M') if visit.visit_time else '',
                'visit_type': visit.visit_type,
            },
            'vitals': {
                'weight': str(vitals.weight) if vitals and vitals.weight else '',
                'height': str(vitals.height) if vitals and vitals.height else '',
                'temperature': str(vitals.temperature) if vitals and vitals.temperature else '',
                'heart_rate': str(vitals.heart_rate) if vitals and vitals.heart_rate else '',
                'pulse_rate': str(vitals.pulse_rate) if vitals and vitals.pulse_rate else '',
                'blood_pressure': vitals.blood_pressure if vitals and vitals.blood_pressure else '',
                'spo2': str(vitals.spo2) if vitals and vitals.spo2 else '',
                'chief_complaint': vitals.chief_complaint if vitals and vitals.chief_complaint else '',
                'respiratory_rate': str(vitals.respiratory_rate) if vitals and vitals.respiratory_rate else '',
                'bottle_feed': vitals.bottle_feed if vitals and vitals.bottle_feed else '',
            },
            'doctor': {
                'name': f"Dr. {request.user.first_name} {request.user.last_name}",
                'phone_number': request.user.phone_number or '',
                'degrees': "M.B.B.S., M.D. (Pediatrics)",
                'reg_no': "MP-17921",
                'speciality': "Pediatrician",
                'prev_docs': [
                    "इंदिरा गाँधी मेडिकल कॉलेज, नागपुर",
                    "गजरा राजा मेडिकल कॉलेज, ग्वालियर",
                    "गांधी मेडिकल कॉलेज, भोपाल",
                    "रेनबो चिल्ड्रेन हॉस्पिटल, भोपाल"
                ]
            },
            'hospital': hospital_info
        }

        with transaction.atomic():
            prescription, created = Prescription.objects.update_or_create(
                visit=visit,
                defaults={
                    'patient': patient,
                    'doctor': request.user,
                    'image': image_file,
                    'snapshot_data': snapshot,
                    'canvas_data': canvas_data,
                },
            )
            # Automatically update patient status to Completed
            visit.status = OPDVisit.StatusChoices.COMPLETED
            visit.save()

        action = 'created' if created else 'updated'
        logger.info(f'Prescription {action} for Visit {visit_id} by {request.user}.')
        return JsonResponse({'status': 'success', 'action': action})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload.'}, status=400)
    except Exception as e:
        logger.exception('Error saving handwritten prescription.')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def recommend_ipd(request):
    patient_id = request.GET.get('patient_id')
    visit_id = request.GET.get('visit_id')
    if visit_id:
        visit = get_object_or_404(OPDVisit, id=visit_id)
        visit.status = OPDVisit.StatusChoices.IPD_RECOMMENDED
        visit.save()
    
    # Redirect to doctor's IPD Patients queue page
    return redirect(reverse('doctor:ipd_patients'))


@login_required
def ipd_patients(request):
    ipd_visits = OPDVisit.objects.filter(
        status__in=[OPDVisit.StatusChoices.IPD_RECOMMENDED, OPDVisit.StatusChoices.ADMITTED]
    ).select_related('patient', 'vitals').order_by('-updated_at')
    
    context = {
        'active_nav': 'ipd_patients',
        'ipd_visits': ipd_visits,
        'base_template': 'doctor/base_doctor.html',
    }
    return render(request, "doctor/ipd_patients.html", context)


@login_required
def discharge_patient(request):
    visit_id = request.GET.get('visit_id')
    if visit_id:
        visit = get_object_or_404(OPDVisit, id=visit_id)
        from receptionist.models import IPDAdmission
        admission = IPDAdmission.objects.filter(visit=visit, status='Admitted').first()
        if admission:
            admission.status = 'Ready for Billing'
            admission.save()
            visit.status = OPDVisit.StatusChoices.READY_FOR_BILLING
            visit.save()
            return redirect(reverse('doctor:ipd_patients'))
        else:
            visit.status = OPDVisit.StatusChoices.DISCHARGED
            visit.save()
    
    # Redirect to doctor's todays patients page (doctor:queue)
    return redirect(reverse('doctor:queue'))

