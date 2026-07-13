from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Patient, OPDVisit

User = get_user_model()


class PatientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testreceptionist",
            email="receptionist@vatsalyashree.com",
            password="testpassword123",
            role=User.Role.RECEPTIONIST
        )

    def test_patient_creation_and_uhid_generation(self):
        patient = Patient.objects.create(
            full_name="John Doe",
            date_of_birth=date(1990, 5, 15),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9876543210",
            address="123 Street, Indore",
            created_by=self.user
        )
        self.assertIsNotNone(patient.uhid)
        self.assertTrue(patient.uhid.startswith("LC-"))
        self.assertEqual(patient.uhid, "LC-10000")  # Sequence starts at 10000

    def test_multiple_patients_increment_uhid(self):
        patient1 = Patient.objects.create(
            full_name="Patient One",
            date_of_birth=date(2000, 1, 1),
            gender=Patient.GenderChoices.FEMALE,
            mobile_number="9999999991",
            address="Address One"
        )
        patient2 = Patient.objects.create(
            full_name="Patient Two",
            date_of_birth=date(2000, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9999999992",
            address="Address Two"
        )
        self.assertEqual(patient1.uhid, "LC-10000")
        self.assertEqual(patient2.uhid, "LC-10001")

    def test_age_property_calculation(self):
        today = date.today()
        
        # Test 5 years old
        dob_5 = today - timedelta(days=5 * 365 + 10)
        patient_5 = Patient(date_of_birth=dob_5)
        self.assertIn("5 Years", patient_5.age)

        # Test 10 months old
        year = today.year
        month = today.month - 10
        if month <= 0:
            month += 12
            year -= 1
        dob_10m = date(year, month, 1)
        patient_10m = Patient(date_of_birth=dob_10m)
        self.assertIn("10 Months", patient_10m.age)

        # Test new-born (e.g. 5 days old)
        dob_5d = today - timedelta(days=5)
        patient_5d = Patient(date_of_birth=dob_5d)
        self.assertEqual("5 Days", patient_5d.age)

    def test_dob_validation_in_future(self):
        future_dob = date.today() + timedelta(days=1)
        patient = Patient(
            full_name="Future Child",
            date_of_birth=future_dob,
            gender=Patient.GenderChoices.OTHER,
            mobile_number="9876543210",
            address="Address"
        )
        with self.assertRaises(ValidationError):
            patient.full_clean()

    def test_mobile_number_validation(self):
        # Invalid mobile number (too short)
        patient = Patient(
            full_name="John Doe",
            date_of_birth=date(1990, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="1234",
            address="Address"
        )
        with self.assertRaises(ValidationError):
            patient.full_clean()


class OPDVisitModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testreceptionist2",
            email="receptionist2@vatsalyashree.com",
            password="testpassword123",
            role=User.Role.RECEPTIONIST
        )
        self.patient = Patient.objects.create(
            full_name="John Doe",
            date_of_birth=date(1990, 5, 15),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9876543210",
            address="123 Street, Indore"
        )

    def test_opd_visit_creation_and_generation(self):
        visit = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user
        )
        self.assertIsNotNone(visit.opd_number)
        self.assertTrue(visit.opd_number.startswith("OPD-"))
        self.assertEqual(visit.opd_number, "OPD-00001")

    def test_multiple_opd_visits_increment_number(self):
        visit1 = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.WAITING
        )
        visit2 = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="11:00:00",
            visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
            status=OPDVisit.StatusChoices.WAITING
        )
        self.assertEqual(visit1.opd_number, "OPD-00001")
        self.assertEqual(visit2.opd_number, "OPD-00002")


from .forms import PatientRegistrationForm, OPDVisitForm

class FormsTest(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            full_name="Jane Doe",
            date_of_birth=date(1995, 8, 20),
            gender=Patient.GenderChoices.FEMALE,
            mobile_number="9876543211",
            address="456 Street, Indore"
        )

    def test_patient_registration_form_valid(self):
        form_data = {
            'full_name': 'Alice Smith',
            'father_name': 'Bob Smith',
            'date_of_birth': '2010-04-05',
            'gender': Patient.GenderChoices.FEMALE,
            'mobile_number': '+91 99887 76655',
            'address': '789 Road, Indore'
        }
        form = PatientRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['mobile_number'], '+919988776655')

    def test_patient_registration_form_invalid_dob(self):
        form_data = {
            'full_name': 'Alice Smith',
            'date_of_birth': '2030-04-05',  # Future date
            'gender': Patient.GenderChoices.FEMALE,
            'mobile_number': '9988776655',
            'address': '789 Road, Indore'
        }
        form = PatientRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_patient_registration_form_invalid_mobile(self):
        form_data = {
            'full_name': 'Alice Smith',
            'date_of_birth': '2010-04-05',
            'gender': Patient.GenderChoices.FEMALE,
            'mobile_number': '123',  # Too short
            'address': '789 Road, Indore'
        }
        form = PatientRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('mobile_number', form.errors)

    def test_opd_visit_form_valid(self):
        form_data = {
            'patient': self.patient.id,
            'visit_date': '2026-07-14',
            'visit_time': '10:30',
            'visit_type': OPDVisit.VisitTypeChoices.NEW_VISIT,
            'status': OPDVisit.StatusChoices.WAITING
        }
        form = OPDVisitForm(data=form_data)
        self.assertTrue(form.is_valid())


from django.urls import reverse

class PatientRegistrationViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="receptionist_test",
            email="receptionist_test@vatsalyashree.com",
            password="password123",
            role=User.Role.RECEPTIONIST
        )
        self.doctor = User.objects.create_user(
            username="doctor_test",
            email="doctor_test@vatsalyashree.com",
            password="password123",
            role=User.Role.DOCTOR
        )
        self.url = reverse('receptionist:patient_registration')

    def test_unauthorized_access(self):
        # GET request without login should redirect to login page
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

        # User logged in but without RECEPTIONIST role should redirect to login page
        self.client.login(email="doctor_test@vatsalyashree.com", password="password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_registration_page(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('patient_form', response.context)
        self.assertIn('visit_form', response.context)
        visit_form = response.context['visit_form']
        self.assertTrue(visit_form.fields['visit_date'].widget.attrs.get('readonly'))
        self.assertTrue(visit_form.fields['visit_time'].widget.attrs.get('readonly'))

    def test_post_registration_success(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        post_data = {
            'full_name': 'New Patient',
            'date_of_birth': '2015-06-10',
            'gender': Patient.GenderChoices.MALE,
            'mobile_number': '9876543219',
            'address': 'Street 1, City',
            'visit_type': OPDVisit.VisitTypeChoices.NEW_VISIT,
            'status': OPDVisit.StatusChoices.WAITING
        }
        response = self.client.post(self.url, data=post_data)
        
        # Verify Patient and OPDVisit objects are created
        patient = Patient.objects.filter(mobile_number='9876543219').first()
        self.assertIsNotNone(patient)
        self.assertEqual(patient.full_name, 'New Patient')
        
        # Verify redirect to opd receipt page
        self.assertRedirects(response, reverse('receptionist:opd_receipt', kwargs={'patient_id': patient.id}))
        
        visit = OPDVisit.objects.filter(patient=patient).first()
        self.assertIsNotNone(visit)
        self.assertEqual(visit.visit_type, OPDVisit.VisitTypeChoices.NEW_VISIT)
        self.assertEqual(visit.created_by, self.user)

    def test_post_registration_reuse_patient(self):
        # Create an existing patient first
        existing_patient = Patient.objects.create(
            full_name="Existing Patient",
            date_of_birth=date(1990, 1, 1),
            gender=Patient.GenderChoices.FEMALE,
            mobile_number="9876543219",
            address="Old Address"
        )
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        post_data = {
            'full_name': 'Existing Patient',
            'date_of_birth': '1990-01-01',
            'gender': Patient.GenderChoices.FEMALE,
            'mobile_number': '9876543219',
            'address': 'Old Address',
            'visit_type': OPDVisit.VisitTypeChoices.FOLLOW_UP,
            'status': OPDVisit.StatusChoices.WAITING
        }
        response = self.client.post(self.url, data=post_data)
        
        # Verify redirect to opd receipt page
        self.assertRedirects(response, reverse('receptionist:opd_receipt', kwargs={'patient_id': existing_patient.id}))
        
        # Verify that no duplicate patient was created
        patients_count = Patient.objects.filter(mobile_number='9876543219').count()
        self.assertEqual(patients_count, 1)
        
        # Verify visit was created for this patient
        visit = OPDVisit.objects.filter(patient=existing_patient).first()
        self.assertIsNotNone(visit)
        self.assertEqual(visit.visit_type, OPDVisit.VisitTypeChoices.FOLLOW_UP)


class ReceiptViewTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email="receptionist_test@vatsalyashree.com",
            username="receptionist_test",
            password="password123",
            role="RECEPTIONIST"
        )
        self.patient = Patient.objects.create(
            full_name="Receipt Patient",
            date_of_birth=date(2000, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9876543210",
            address="Guna"
        )
        self.visit = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="10:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user,
            updated_by=self.user
        )
        self.url = reverse('receptionist:opd_receipt', kwargs={'patient_id': self.patient.id})

    def test_receipt_view_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_receipt_view_success(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "receptionist/receipt.html")
        self.assertEqual(response.context['patient'], self.patient)
        self.assertEqual(response.context['visit'], self.visit)
        self.assertEqual(response.context['consultation_fee'], 200)

