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
