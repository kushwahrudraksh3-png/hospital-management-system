from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from receptionist.models import Patient, OPDVisit

User = get_user_model()

class PatientSearchFiltersTest(TestCase):
    def setUp(self):
        # Create a doctor user
        self.user = User.objects.create_user(
            username="testdoctor",
            email="doctor@vatsalyashree.com",
            password="password123",
            role="DOCTOR"
        )
        self.client.login(email="doctor@vatsalyashree.com", password="password123")
        
        # Create patients
        self.patient_new = Patient.objects.create(
            full_name="New Patient Test",
            date_of_birth=date(1995, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9876543210",
            address="Address 1",
            father_name="Father A"
        )
        
        self.patient_followup = Patient.objects.create(
            full_name="Followup Patient Test",
            date_of_birth=date(1996, 1, 1),
            gender=Patient.GenderChoices.FEMALE,
            mobile_number="9876543211",
            address="Address 2",
            father_name="Father B"
        )
        
        # Create visits for self.patient_new:
        # Latest visit is a "New Visit"
        OPDVisit.objects.create(
            patient=self.patient_new,
            visit_date=date.today() - timedelta(days=2),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.COMPLETED,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create visits for self.patient_followup:
        # Visit 1: New Visit (older)
        OPDVisit.objects.create(
            patient=self.patient_followup,
            visit_date=date.today() - timedelta(days=5),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.COMPLETED,
            created_by=self.user,
            updated_by=self.user
        )
        # Visit 2: Follow-up (latest)
        OPDVisit.objects.create(
            patient=self.patient_followup,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.url = reverse('doctor:patient_search')

    def test_search_all_patients(self):
        response = self.client.get(self.url, {'patient_type': 'all'})
        self.assertEqual(response.status_code, 200)
        patients = list(response.context['patients'])
        self.assertEqual(len(patients), 2)

    def test_filter_new_patients(self):
        response = self.client.get(self.url, {'patient_type': 'new'})
        self.assertEqual(response.status_code, 200)
        patients = list(response.context['patients'])
        self.assertEqual(len(patients), 1)
        self.assertEqual(patients[0].id, self.patient_new.id)

    def test_filter_followup_patients(self):
        response = self.client.get(self.url, {'patient_type': 'followup'})
        self.assertEqual(response.status_code, 200)
        patients = list(response.context['patients'])
        self.assertEqual(len(patients), 1)
        self.assertEqual(patients[0].id, self.patient_followup.id)

    def test_search_and_filter_combined(self):
        # Search for 'Followup' under 'followup' filter
        response = self.client.get(self.url, {'patient_type': 'followup', 'q': 'Followup'})
        self.assertEqual(response.status_code, 200)
        patients = list(response.context['patients'])
        self.assertEqual(len(patients), 1)
        self.assertEqual(patients[0].id, self.patient_followup.id)
        
        # Search for 'New' under 'followup' filter (should return nothing)
        response = self.client.get(self.url, {'patient_type': 'followup', 'q': 'New'})
        self.assertEqual(response.status_code, 200)
        patients = list(response.context['patients'])
        self.assertEqual(len(patients), 0)


class AutoSavePrescriptionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="doc1",
            email="doc1@vatsalyashree.com",
            password="password123",
            role="DOCTOR"
        )
        self.client.login(email="doc1@vatsalyashree.com", password="password123")
        self.patient = Patient.objects.create(
            full_name="Prescription Test Patient",
            date_of_birth=date(2020, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9998887770",
            address="Test Address"
        )
        self.visit = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.READY_FOR_DOCTOR,
            created_by=self.user,
            updated_by=self.user
        )
        self.dummy_image_data = (
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
            "AAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

    def test_save_prescription_creates_and_updates_without_duplicates(self):
        import json
        from doctor.models import Prescription

        url = reverse('doctor:save_prescription')
        payload = {
            'visit_id': str(self.visit.id),
            'patient_id': str(self.patient.id),
            'image_data': self.dummy_image_data,
            'canvas_data': [{'points': [{'x': 0.1, 'y': 0.2}]}]
        }

        # 1. Save prescription for first time
        resp1 = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json().get('status'), 'success')
        self.assertEqual(resp1.json().get('action'), 'created')
        self.assertEqual(Prescription.objects.filter(visit=self.visit).count(), 1)

        # 2. Save prescription second time (update existing, no duplicates)
        payload['canvas_data'] = [{'points': [{'x': 0.1, 'y': 0.2}, {'x': 0.3, 'y': 0.4}]}]
        resp2 = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json().get('status'), 'success')
        self.assertEqual(resp2.json().get('action'), 'updated')
        self.assertEqual(Prescription.objects.filter(visit=self.visit).count(), 1)

    def test_proceed_to_lab_navigation_and_lab_request_creation(self):
        import json
        self.client.post(
            reverse('doctor:save_prescription'),
            data=json.dumps({
                'visit_id': str(self.visit.id),
                'patient_id': str(self.patient.id),
                'image_data': self.dummy_image_data,
                'canvas_data': [{'points': [{'x': 0.1, 'y': 0.2}]}]
            }),
            content_type='application/json'
        )
        lab_url = f"{reverse('doctor:report_list')}?visit_id={self.visit.id}&patient_id={self.patient.id}"
        response = self.client.get(lab_url)
        self.assertEqual(response.status_code, 200)

    def test_proceed_to_ipd_navigation_and_status_update(self):
        import json
        self.client.post(
            reverse('doctor:save_prescription'),
            data=json.dumps({
                'visit_id': str(self.visit.id),
                'patient_id': str(self.patient.id),
                'image_data': self.dummy_image_data,
                'canvas_data': [{'points': [{'x': 0.1, 'y': 0.2}]}]
            }),
            content_type='application/json'
        )
        ipd_url = f"{reverse('doctor:recommend_ipd')}?patient_id={self.patient.id}&visit_id={self.visit.id}"
        response = self.client.get(ipd_url)
        self.assertEqual(response.status_code, 302)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, OPDVisit.StatusChoices.IPD_RECOMMENDED)


class DoctorQueueFiltersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="docqueue",
            email="docqueue@vatsalyashree.com",
            password="password123",
            role="DOCTOR"
        )
        self.client.login(email="docqueue@vatsalyashree.com", password="password123")
        
        self.patient = Patient.objects.create(
            full_name="Queue Test Patient",
            date_of_birth=date(2010, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9998887771",
            address="Test Address"
        )

    def test_queue_context_contains_today(self):
        url = reverse('doctor:queue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('today', response.context)
        self.assertEqual(response.context['today'], date.today())

    def test_followup_visits_in_queue_without_vitals(self):
        # Create a Follow-up visit today without vitals
        visit_today = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create a New Visit today without vitals (should be excluded)
        visit_new = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="11:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create a Follow-up visit yesterday without vitals (should be excluded)
        visit_yesterday = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today() - timedelta(days=1),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user,
            updated_by=self.user
        )

        url = reverse('doctor:queue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        today_visits = list(response.context['today_visits'])
        # Only the today's follow-up visit should be present, not the new or yesterday's follow-up visit.
        self.assertIn(visit_today, today_visits)
        self.assertNotIn(visit_new, today_visits)
        self.assertNotIn(visit_yesterday, today_visits)


