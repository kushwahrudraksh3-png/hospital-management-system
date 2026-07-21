from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps
from django.utils import timezone
from receptionist.models import OPDVisit
from lab.models import LaboratoryRequest

def lab_required(view_func):
    """Decorator that checks user is authenticated and has LAB_ADMINISTRATOR role or is admin/superuser."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ["LAB_ADMINISTRATOR", "ADMIN"] and not request.user.is_superuser:
            messages.error(request, "Access denied. Laboratory role required.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)
    return wrapper

@lab_required
def dashboard(request):
    from datetime import datetime, timedelta
    
    today = timezone.localdate()
    
    # Parse and validate selected date
    date_str = request.GET.get('date')
    selected_date = today
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    # Calculate metric card counts
    from receptionist.models import Patient
    from lab.models import LaboratoryReport
    from django.db.models import Q
    
    # Helper to retrieve lab visits for a specific date (referred, billed, or cased)
    def get_lab_patients_query(date):
        return OPDVisit.objects.filter(
            visit_date=date
        ).filter(
            Q(status=OPDVisit.StatusChoices.PENDING_LAB) |
            Q(laboratory_bill__isnull=False) |
            Q(laboratory_case__isnull=False)
        ).distinct()

    todays_patients_count = get_lab_patients_query(selected_date).count()
    
    pending_billing_count = get_lab_patients_query(selected_date).filter(
        laboratory_bill__isnull=True
    ).count()
    
    reports_completed_count = LaboratoryReport.objects.filter(
        visit__visit_date=today,
        status__in=['COMPLETED', 'SENT']
    ).count()
    
    all_patients_count = Patient.objects.filter(
        Q(visits__status=OPDVisit.StatusChoices.PENDING_LAB) |
        Q(laboratory_bills__isnull=False) |
        Q(laboratory_cases__isnull=False)
    ).distinct().count()
    
    # Calculate patient percentage change compared to the previous day
    previous_day = selected_date - timedelta(days=1)
    previous_patients_count = get_lab_patients_query(previous_day).count()
    
    if previous_patients_count > 0:
        patient_percent_change = int(((todays_patients_count - previous_patients_count) / previous_patients_count) * 100)
    else:
        patient_percent_change = 0
    patient_change_abs = abs(patient_percent_change)
    
    context = {
        "active_nav": "dashboard",
        "todays_patients_count": todays_patients_count,
        "pending_billing_count": pending_billing_count,
        "reports_completed_count": reports_completed_count,
        "all_patients_count": all_patients_count,
        "patient_percent_change": patient_percent_change,
        "patient_change_abs": patient_change_abs,
        "selected_date": selected_date,
        "today": today,
        "current_time_str": timezone.localtime().strftime("%I:%M %p"),
    }
    
    return render(request, "lab/dashboard.html", context)

@lab_required
def todays_patients(request):
    from lab.models import LaboratoryBill, LaboratoryCase, LaboratoryReport
    from django.db.models import Q
    today = timezone.localdate()
    
    # Query LaboratoryRequest (proxy for OPDVisit) for today's visits sent to lab by doctor
    raw_requests = LaboratoryRequest.objects.filter(
        visit_date=today
    ).filter(
        Q(status=OPDVisit.StatusChoices.PENDING_LAB) |
        Q(laboratory_bill__isnull=False) |
        Q(laboratory_case__isnull=False)
    ).distinct().select_related(
        'patient', 
        'handwritten_prescription__doctor',
        'laboratory_bill'
    ).order_by('-updated_at')
    
    lab_requests = []
    for req in raw_requests:
        # Get all billed lab tests (excluding X-Rays)
        bill = getattr(req, 'laboratory_bill', None)
        
        if not bill:
            req.status_code = 'bill_pending'
            req.status_text = 'Bill Pending'
            req.status_class = 'badge bg-secondary'
            lab_requests.append(req)
            continue
            
        # Get or create the case
        case, _ = LaboratoryCase.objects.get_or_create(
            visit=req,
            defaults={'patient': req.patient}
        )
        
        bill_items = [item for item in bill.items.all() if item.test and "x-ray" not in item.test.name.lower()]
        if not bill_items:
            # If the bill only has X-Rays or no tests, skip it from Today's Patients lab queue
            continue
            
        # Ensure LaboratoryReport records are initialized for each test
        for item in bill_items:
            LaboratoryReport.objects.get_or_create(
                case=case,
                patient=req.patient,
                visit=req,
                lab_test=item.test,
                defaults={'status': 'PENDING'}
            )
            
        case_reports = LaboratoryReport.objects.filter(case=case).exclude(lab_test__name__icontains="x-ray")
        
        # Determine status code, text, and bootstrap badge class
        has_reports = case_reports.exists()
        is_pending = case_reports.filter(status__in=['PENDING', 'IN_PROGRESS']).exists()
        
        if has_reports and not is_pending:
            req.status_code = 'sent'
            req.status_text = 'Sent to Doctor'
            req.status_class = 'badge bg-success'
        else:
            req.status_code = 'progress'
            req.status_text = 'In Progress'
            req.status_class = 'badge bg-warning text-dark'
            
        lab_requests.append(req)
        
    return render(request, "lab/todays_patients.html", {
        "active_nav": "todays_patients",
        "lab_requests": lab_requests,
        "today": today,
    })

@lab_required
def completed_reports(request):
    from .models import LaboratoryReport
    reports = LaboratoryReport.objects.filter(
        status__in=['COMPLETED', 'SENT']
    ).exclude(
        lab_test__name__icontains="x-ray"
    ).select_related(
        'patient', 'visit__handwritten_prescription__doctor', 'lab_test', 'visit__laboratory_bill'
    ).order_by('-created_at')
    
    return render(request, "lab/completed_reports.html", {
        "active_nav": "completed_reports",
        "reports": reports
    })

def populate_default_tests():
    from .models import LabTest
    TEST_DATA = [
        ("CBC", 250),
        ("C.R.P.", 250),
        ("Malaria Antigen (Card)", 150),
        ("Widal", 150),
        ("Urine R/M", 100),
        ("Blood Group", 50),
        ("SGPT", 150),
        ("Calcium", 150),
        ("Bilirubin", 150),
        ("Urea", 100),
        ("R.B.S.", 50),
        ("Creatinine", 100),
        ("Mantoux", 150),
        ("A.E.C.", 100),
        ("P.T. INR", 300),
        ("VDRL", 150),
        ("Stool R/M", 250),
        ("X-Ray (Per Film)", 400),
        ("Dengue Ag/Ab", 600),
        ("BT.CT.", 150),
        ("HBsAg", 200),
        ("HIV", 300),
        ("Na⁺ / K⁺ / Cl⁻", 300),
        ("G6PD", 300),
        ("Chikungunya", 600),
        ("T3, T4, TSH", 600),
        ("Lipid Profile", 600),
        ("Total Serum Protein", 250),
        ("E.S.R.", 100),
        ("SGOT", 150),
        ("Sickling Test", 300),
        ("LFT (Liver Function Test)", 700),
        ("RFT (Renal Function Test)", 700),
        ("Scrub Typhus", 400),
        ("IgE Level", 500),
    ]
    try:
        for name, price in TEST_DATA:
            LabTest.objects.get_or_create(name=name, defaults={"price": price, "is_active": True})
    except Exception:
        pass

@lab_required
def lab_billing(request):
    from doctor.models import Prescription
    from .models import LabTest, LaboratoryBill, LaboratoryBillItem
    from django.db import transaction
    from django.shortcuts import redirect
    from django.urls import reverse
    
    populate_default_tests()
    
    visit_id = request.GET.get('visit_id') or request.POST.get('visit_id')
    patient_id = request.GET.get('patient_id') or request.POST.get('patient_id')
    
    visit = None
    if visit_id:
        visit = OPDVisit.objects.filter(id=visit_id).select_related('patient', 'vitals', 'handwritten_prescription').first()
    elif patient_id:
        visit = OPDVisit.objects.filter(patient_id=patient_id).select_related('patient', 'vitals', 'handwritten_prescription').order_by('-visit_date', '-visit_time').first()
        
    prescription = getattr(visit, 'handwritten_prescription', None) if visit else None
    
    if request.method == "POST" and visit:
        test_ids = request.POST.getlist('tests')
        if test_ids:
            with transaction.atomic():
                bill, created = LaboratoryBill.objects.get_or_create(
                    visit=visit,
                    defaults={'patient': visit.patient}
                )
                
                # Clear existing items if updating
                bill.items.all().delete()
                
                selected_tests = LabTest.objects.filter(id__in=test_ids, is_active=True)
                grand_total = 0
                bill_items = []
                for test in selected_tests:
                    grand_total += test.price
                    bill_items.append(LaboratoryBillItem(
                        bill=bill,
                        test=test,
                        name=test.name,
                        price=test.price
                    ))
                
                LaboratoryBillItem.objects.bulk_create(bill_items)
                bill.grand_total = grand_total
                bill.save()
                
                return redirect(f"{reverse('lab:bill_receipt')}?bill_id={bill.id}")
    
    active_tests = LabTest.objects.filter(is_active=True).order_by('name')
    
    context = {
        "active_nav": "lab_billing",
        "visit": visit,
        "patient": visit.patient if visit else None,
        "prescription": prescription,
        "visit_id": visit_id,
        "patient_id": patient_id,
        "active_tests": active_tests,
    }
    return render(request, "lab/lab_billing.html", context)

@lab_required
def bill_receipt(request):
    from .models import LaboratoryBill
    bill_id = request.GET.get('bill_id')
    bill = None
    if bill_id:
        bill = LaboratoryBill.objects.filter(id=bill_id).select_related('patient', 'visit__handwritten_prescription__doctor').prefetch_related('items').first()
    if not bill:
        bill = LaboratoryBill.objects.all().select_related('patient', 'visit__handwritten_prescription__doctor').prefetch_related('items').first()
        
    items = bill.items.all() if bill else []
    remaining_rows_count = max(0, 9 - len(items))
    
    context = {
        "active_nav": "lab_billing",
        "bill": bill,
        "patient": bill.patient if bill else None,
        "visit": bill.visit if bill else None,
        "items": items,
        "remaining_rows": range(remaining_rows_count),
    }
    return render(request, "lab/bill_receipt.html", context)

@lab_required
def total_billing_patients(request):
    from .models import LaboratoryBill
    from django.utils import timezone
    from django.db.models import Q
    
    today = timezone.localdate()
    filter_type = request.GET.get('filter', 'today')
    search_query = request.GET.get('q', '').strip()
    
    bills_qs = LaboratoryBill.objects.all().select_related(
        'patient', 
        'visit__handwritten_prescription__doctor'
    ).prefetch_related('items').order_by('-created_at')
    
    if filter_type == 'today':
        bills_qs = bills_qs.filter(created_at__date=today)
        
    if search_query:
        bills_qs = bills_qs.filter(
            Q(patient__full_name__icontains=search_query) |
            Q(patient__uhid__icontains=search_query) |
            Q(visit__opd_number__icontains=search_query) |
            Q(bill_number__icontains=search_query)
        )
        
    for bill in bills_qs:
        bill.total_tests = bill.items.count()
        
    context = {
        "active_nav": "total_billing_patients",
        "bills": bills_qs,
        "filter_type": filter_type,
        "search_query": search_query,
        "today": today,
    }
    return render(request, "lab/total_billing_patients.html", context)

@lab_required
def report_entry(request):
    from .models import LaboratoryBill, LaboratoryCase, LaboratoryReport, LabTest, LabTestParameter
    from django.db.models import Prefetch
    from django.contrib import messages
    
    visit_id = request.GET.get('visit_id') or request.POST.get('visit_id')
    patient_id = request.GET.get('patient_id') or request.POST.get('patient_id')
    bill_id = request.GET.get('bill_id') or request.POST.get('bill_id')
    lab_test_id = request.GET.get('lab_test_id') or request.POST.get('lab_test_id')
    action = request.GET.get('action')
    report_id = request.GET.get('report_id')
    
    # Handle "Save & Send to Doctor" action from preview page
    if action == 'send_to_doctor':
        if report_id:
            LaboratoryReport.objects.filter(id=report_id).update(status='SENT')
        elif visit_id:
            LaboratoryReport.objects.filter(visit_id=visit_id).update(status='SENT')
        messages.success(request, "Report successfully saved and sent to doctor.")
        return redirect("lab:report_entry")
        
    if visit_id or patient_id or bill_id:
        visit = None
        if visit_id:
            visit = OPDVisit.objects.filter(id=visit_id).select_related('patient', 'handwritten_prescription__doctor').first()
        elif bill_id:
            bill = LaboratoryBill.objects.filter(id=bill_id).select_related('visit__patient', 'visit__handwritten_prescription__doctor').first()
            if bill:
                visit = bill.visit
        elif patient_id:
            visit = OPDVisit.objects.filter(patient_id=patient_id).select_related('patient', 'handwritten_prescription__doctor').order_by('-visit_date', '-visit_time').first()
        
        patient = visit.patient if visit else None
        bill = getattr(visit, 'laboratory_bill', None) if visit else None
        if not bill and visit:
            bill = LaboratoryBill.objects.filter(visit=visit).first()
            
        case = None
        if visit:
            case, created = LaboratoryCase.objects.get_or_create(
                visit=visit,
                defaults={'patient': patient}
            )
            
        if case and bill:
            for item in bill.items.all():
                if item.test and "x-ray" not in item.test.name.lower():
                    LaboratoryReport.objects.get_or_create(
                        case=case,
                        patient=patient,
                        visit=visit,
                        lab_test=item.test,
                        defaults={'status': 'PENDING'}
                    )
                    
        # Fetch all reports for this case to list billed investigations, excluding X-Ray
        reports = []
        if case:
            reports = LaboratoryReport.objects.filter(case=case).exclude(lab_test__name__icontains="x-ray").select_related('lab_test').prefetch_related(
                Prefetch(
                    'lab_test__parameters',
                    queryset=LabTestParameter.objects.filter(is_active=True).order_by('display_order'),
                    to_attr='active_parameters'
                ),
                'results'
            )
            
        # Build test data containing test, report, and parameters with draft values
        test_data = []
        for r in reports:
            results_dict = {res.parameter_id: res.result_value for res in r.results.all()}
            parameters = []
            for param in r.lab_test.active_parameters:
                param.draft_value = results_dict.get(param.id, "")
                parameters.append(param)
            test_data.append({
                'report': r,
                'test': r.lab_test,
                'parameters': parameters
            })
            
        # Also compute non_xray_reports_count for the template header details
        case.non_xray_reports_count = len(reports)
            
        context = {
            "active_nav": "report_entry",
            "visit": visit,
            "patient": patient,
            "bill": bill,
            "case": case,
            "test_data": test_data,
            "show_form": True,
            "initial_test_id": lab_test_id,
        }
        return render(request, "lab/report_entry.html", context)
    else:
        # Fetch today's LaboratoryBills to build the queue dynamically
        today = timezone.localdate()
        all_bills = LaboratoryBill.objects.filter(
            created_at__date=today
        ).select_related(
            'patient', 'visit__handwritten_prescription__doctor'
        ).prefetch_related('items__test').order_by('-created_at')
        
        pending_cases = []
        completed_cases = []
        
        for bill in all_bills:
            # Only include bills that have at least one laboratory investigation item (excluding X-Rays)
            bill_items = [item for item in bill.items.all() if item.test and "x-ray" not in item.test.name.lower()]
            has_investigation = len(bill_items) > 0
            if not has_investigation:
                continue
                
            # Automatically get or create the LaboratoryCase for this bill/visit
            case, created = LaboratoryCase.objects.get_or_create(
                visit=bill.visit,
                defaults={'patient': bill.patient}
            )
            
            # Pre-initialize LaboratoryReport for each test item if not already exists (excluding X-Rays)
            for item in bill_items:
                LaboratoryReport.objects.get_or_create(
                    case=case,
                    patient=bill.patient,
                    visit=bill.visit,
                    lab_test=item.test,
                    defaults={'status': 'PENDING'}
                )
            
            # Fetch all reports associated with this case (excluding X-Rays)
            case_reports = [r for r in case.reports.all() if "x-ray" not in r.lab_test.name.lower()]
            
            # A patient remains in the pending queue until all investigations are completed or sent
            is_pending = False
            if not case_reports:
                is_pending = True
            else:
                for report in case_reports:
                    if report.status in ['PENDING', 'IN_PROGRESS']:
                        is_pending = True
                        break
            
            # Attach the bill object and report count to the case for the template to render
            case.bill = bill
            case.non_xray_reports_count = len(case_reports)
            
            if is_pending:
                pending_cases.append(case)
            else:
                completed_cases.append(case)
                
        context = {
            "active_nav": "report_entry",
            "pending_cases": pending_cases,
            "completed_cases": completed_cases,
            "pending_count": len(pending_cases),
            "completed_count": len(completed_cases),
            "show_form": False,
        }
        return render(request, "lab/report_entry.html", context)

@login_required
def report_preview(request):
    from receptionist.models import Patient, OPDVisit
    from .models import LaboratoryBill, LaboratoryReport, LaboratoryReportResult, LabTest, LabTestParameter
    from datetime import date
    from django.utils import timezone
    
    patient_id = request.GET.get('patient_id')
    visit_id = request.GET.get('visit_id')
    bill_id = request.GET.get('bill_id')
    report_id = request.GET.get('report_id')
    
    report = None
    if report_id:
        report = LaboratoryReport.objects.filter(id=report_id).select_related(
            'patient', 'visit__handwritten_prescription__doctor', 'lab_test'
        ).first()
    
    if not report:
        q = LaboratoryReport.objects.all().select_related(
            'patient', 'visit__handwritten_prescription__doctor', 'lab_test'
        )
        if bill_id:
            bill = LaboratoryBill.objects.filter(id=bill_id).first()
            if bill:
                q = q.filter(visit=bill.visit)
        elif visit_id:
            q = q.filter(visit_id=visit_id)
        elif patient_id:
            q = q.filter(patient_id=patient_id)
        report = q.order_by('-generated_date').first()

    if not report:
        report = LaboratoryReport.objects.all().select_related(
            'patient', 'visit__handwritten_prescription__doctor', 'lab_test'
        ).order_by('-generated_date').first()
        
    if report:
        patient = report.patient
        visit = report.visit
        bill = LaboratoryBill.objects.filter(visit=visit).first()
        results = report.results.select_related('parameter').order_by('parameter__display_order', 'parameter__parameter_name')
        
        # Calculate dynamic reference ranges
        gender = patient.gender.upper() if (patient and patient.gender) else 'MALE'
        for res in results:
            param = res.parameter
            ref_range = ""
            if gender in ['M', 'MALE']:
                ref_range = param.male_reference_range
            elif gender in ['F', 'FEMALE']:
                ref_range = param.female_reference_range
            
            if not ref_range or not ref_range.strip():
                ref_range = param.common_reference_range
                
            res.resolved_reference_range = ref_range
    else:
        # Fallback if no report exists in the database
        if bill_id:
            bill = LaboratoryBill.objects.filter(id=bill_id).select_related(
                'patient', 'visit__handwritten_prescription__doctor'
            ).first()
        elif visit_id:
            bill = LaboratoryBill.objects.filter(visit_id=visit_id).select_related(
                'patient', 'visit__handwritten_prescription__doctor'
            ).first()
        elif patient_id:
            bill = LaboratoryBill.objects.filter(patient_id=patient_id).select_related(
                'patient', 'visit__handwritten_prescription__doctor'
            ).order_by('-created_at').first()
        else:
            bill = LaboratoryBill.objects.all().select_related(
                'patient', 'visit__handwritten_prescription__doctor'
            ).first()
            
        if bill:
            visit = bill.visit
            patient = bill.patient
            # Get the first test from the bill
            bill_item = bill.items.first()
            lab_test = bill_item.test if bill_item else None
        else:
            # Direct fallbacks
            if visit_id:
                visit = OPDVisit.objects.filter(id=visit_id).select_related('patient', 'handwritten_prescription__doctor').first()
            else:
                visit = OPDVisit.objects.all().select_related('patient', 'handwritten_prescription__doctor').order_by('-visit_date', '-visit_time').first()
            
            if visit:
                patient = visit.patient
            else:
                if patient_id:
                    patient = Patient.objects.filter(id=patient_id).first()
                else:
                    patient = Patient.objects.all().first()
            
            lab_test = LabTest.objects.filter(is_active=True).first()
            
        # Instantiate in-memory fallback objects to guarantee template evaluation succeeds
        if not patient:
            patient = Patient(full_name="Mock Patient", gender="Male", date_of_birth=date(2015, 1, 1))
        
        if not visit:
            visit = OPDVisit(patient=patient, visit_date=date.today(), visit_time=timezone.now().time())
            
        if not lab_test:
            lab_test = LabTest(name="Blood Examination", price=0.0)
            
        report = LaboratoryReport(
            patient=patient,
            visit=visit,
            lab_test=lab_test,
            report_number=bill.bill_number.replace("LB", "LR") if (bill and bill.bill_number) else "LR-DRAFT"
        )
        
        # Create mock results based on LabTestParameter
        parameters = LabTestParameter.objects.filter(lab_test=lab_test, is_active=True)
        results = []
        for param in parameters:
            # Calculate reference range
            gender = patient.gender.upper() if (patient and patient.gender) else 'MALE'
            ref_range = ""
            if gender in ['M', 'MALE']:
                ref_range = param.male_reference_range
            elif gender in ['F', 'FEMALE']:
                ref_range = param.female_reference_range
            
            if not ref_range or not ref_range.strip():
                ref_range = param.common_reference_range
            
            res = LaboratoryReportResult(
                report=report,
                parameter=param,
                result_value="-"
            )
            res.resolved_reference_range = ref_range
            results.append(res)
            
    context = {
        "active_nav": "report_preview",
        "report": report,
        "bill": bill,
        "patient": patient,
        "visit": visit,
        "results": results,
    }
    return render(request, "lab/report_preview.html", context)

@login_required
def report_save(request):
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.db import transaction
    from django.contrib import messages
    from receptionist.models import Patient, OPDVisit
    from .models import LaboratoryBill, LaboratoryReport, LaboratoryReportResult, LabTestParameter, LabTest, LaboratoryCase
    
    if request.method == "POST":
        visit_id = request.POST.get("visit_id")
        patient_id = request.POST.get("patient_id")
        bill_id = request.POST.get("bill_id")
        lab_test_id = request.POST.get("lab_test_id")
        action_type = request.POST.get("action") or request.POST.get("submit_type")
        is_draft = (action_type == "draft")
        
        visit = OPDVisit.objects.filter(id=visit_id).first()
        patient = Patient.objects.filter(id=patient_id).first()
        
        # Step 1: Validate every entered result (non-subheader parameters cannot be empty) ONLY if not a draft
        parameters = LabTestParameter.objects.filter(lab_test_id=lab_test_id, is_active=True)
        if not is_draft:
            errors = []
            for param in parameters:
                if param.parameter_type.lower() != "subheader":
                    val = request.POST.get(f"param_{param.id}", "").strip()
                    if not val:
                        errors.append(f"Result for '{param.parameter_name}' cannot be empty.")
                        
            if errors:
                for err in errors:
                    messages.error(request, err)
                # Redirect back to entry form
                query_str = f"?visit_id={visit_id or ''}&patient_id={patient_id or ''}&bill_id={bill_id or ''}&lab_test_id={lab_test_id or ''}"
                return redirect(reverse("lab:report_entry") + query_str)
            
        with transaction.atomic():
            lab_test_obj = LabTest.objects.filter(id=lab_test_id).first()
            
            case = None
            if visit:
                case, _ = LaboratoryCase.objects.get_or_create(
                    visit=visit,
                    defaults={'patient': patient}
                )
                
            report, created = LaboratoryReport.objects.update_or_create(
                patient=patient,
                visit=visit,
                lab_test=lab_test_obj,
                defaults={
                    "case": case,
                    "status": "IN_PROGRESS" if is_draft else "COMPLETED",
                    "generated_by": request.user if request.user.is_authenticated else None
                }
            )
            
            # Save results
            for param in parameters:
                val = request.POST.get(f"param_{param.id}", "").strip()
                LaboratoryReportResult.objects.update_or_create(
                    report=report,
                    parameter=param,
                    defaults={"result_value": val}
                )
                
        if is_draft:
            messages.success(request, "Draft saved successfully.")
            return redirect("lab:report_entry")
        else:
            # Redirect to report-preview
            url = reverse("lab:report_preview") + f"?report_id={report.id}"
            return redirect(url)
        
    return redirect("lab:report_entry")

@lab_required
def doctor_prescription(request):
    from doctor.models import Prescription
    
    visit_id = request.GET.get('visit_id')
    patient_id = request.GET.get('patient_id')
    
    visit = None
    if visit_id:
        visit = OPDVisit.objects.filter(id=visit_id).select_related('patient', 'vitals', 'handwritten_prescription').first()
    elif patient_id:
        visit = OPDVisit.objects.filter(patient_id=patient_id).select_related('patient', 'vitals', 'handwritten_prescription').order_by('-visit_date', '-visit_time').first()
        
    prescription = getattr(visit, 'handwritten_prescription', None) if visit else None
    saved_image_url = None
    if prescription and prescription.image:
        saved_image_url = prescription.image.url
        
    context = {
        "active_nav": "todays_patients",
        "visit": visit,
        "patient": visit.patient if visit else None,
        "vitals": visit.vitals if visit and hasattr(visit, 'vitals') else None,
        "prescription": prescription,
        "saved_image_url": saved_image_url,
        "visit_id": visit_id,
        "patient_id": patient_id,
    }
    return render(request, "lab/doctor_prescription.html", context)


