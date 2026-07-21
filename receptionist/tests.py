from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Patient, OPDVisit, HospitalSettings

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
            'status': OPDVisit.StatusChoices.WAITING,
            'payment_mode': OPDVisit.PaymentModeChoices.CASH
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
            'status': OPDVisit.StatusChoices.WAITING,
            'payment_mode': OPDVisit.PaymentModeChoices.CASH
        }
        response = self.client.post(self.url, data=post_data)
        
        # Verify Patient and OPDVisit objects are created
        patient = Patient.objects.filter(mobile_number='9876543219').first()
        self.assertIsNotNone(patient)
        self.assertEqual(patient.full_name, 'New Patient')
        
        # Verify that visit has correct payment mode
        visit = OPDVisit.objects.filter(patient=patient).first()
        self.assertIsNotNone(visit)
        self.assertEqual(visit.visit_type, OPDVisit.VisitTypeChoices.NEW_VISIT)
        self.assertEqual(visit.payment_mode, OPDVisit.PaymentModeChoices.CASH)
        self.assertEqual(visit.created_by, self.user)

        # Verify redirect to opd receipt page with query param
        self.assertRedirects(response, f"{reverse('receptionist:opd_receipt', kwargs={'patient_id': patient.id})}?visit_id={visit.id}")

    def test_post_registration_shared_mobile_number(self):
        # Create an existing patient first (Father)
        existing_patient = Patient.objects.create(
            full_name="Father Patient",
            date_of_birth=date(1980, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9876543219",
            address="Family Address"
        )
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        post_data = {
            'full_name': 'Child Patient',
            'date_of_birth': '2012-05-15',
            'gender': Patient.GenderChoices.FEMALE,
            'mobile_number': '9876543219',
            'address': 'Family Address',
            'status': OPDVisit.StatusChoices.WAITING,
            'payment_mode': OPDVisit.PaymentModeChoices.CASH
        }
        response = self.client.post(self.url, data=post_data)
        
        # Verify that 2 distinct patients now exist with the same mobile number
        patients_count = Patient.objects.filter(mobile_number='9876543219').count()
        self.assertEqual(patients_count, 2)
        
        child_patient = Patient.objects.filter(full_name='Child Patient').first()
        self.assertIsNotNone(child_patient)
        self.assertNotEqual(existing_patient.id, child_patient.id)
        self.assertNotEqual(existing_patient.uhid, child_patient.uhid)


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


class PatientListViewTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email="receptionist_test@vatsalyashree.com",
            username="receptionist_test",
            password="password123",
            role="RECEPTIONIST"
        )
        self.url = reverse('receptionist:patient_list')

        # Create multiple patients for pagination and search tests
        self.patients = []
        for i in range(25):
            p = Patient.objects.create(
                full_name=f"Patient {i}",
                date_of_birth=date(1990 + (i % 10), 1, 1),
                gender=Patient.GenderChoices.MALE if i % 2 == 0 else Patient.GenderChoices.FEMALE,
                mobile_number=f"98765432{i:02d}",
                address="Test Address"
            )
            self.patients.append(p)
            
            # create visits for some of them
            if i < 5:
                OPDVisit.objects.create(
                    patient=p,
                    visit_date=date.today(),
                    visit_time="10:00",
                    visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
                    status=OPDVisit.StatusChoices.WAITING,
                    created_by=self.user,
                    updated_by=self.user
                )

    def test_patient_list_view_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_patient_list_view_success_and_pagination(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "receptionist/patient_list.html")
        
        # Verify pagination limit (20 per page)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj.object_list), 20)
        self.assertEqual(response.context['total_patients'], 25)
        self.assertEqual(response.context['today_patients_count'], 5)

    def test_patient_list_view_search_by_name(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(self.url, {'q': 'Patient 12'})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj.object_list), 1)
        self.assertEqual(page_obj.object_list[0].full_name, 'Patient 12')

    def test_patient_list_view_search_by_mobile(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(self.url, {'q': '9876543204'})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj.object_list), 1)
        self.assertEqual(page_obj.object_list[0].mobile_number, '9876543204')

    def test_patient_list_view_search_by_uhid(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        uhid = self.patients[0].uhid
        response = self.client.get(self.url, {'q': uhid})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj.object_list), 1)
        self.assertEqual(page_obj.object_list[0].uhid, uhid)

    def test_patient_list_view_filter_today(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(self.url, {'filter': 'today'})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(page_obj.object_list), 5)


class CreateOPDVisitViewTest(TestCase):
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
            full_name="Existing Patient Test",
            date_of_birth=date(1995, 5, 5),
            gender=Patient.GenderChoices.FEMALE,
            mobile_number="9876543222",
            address="Gwalior"
        )
        self.url = reverse('receptionist:create_opd_visit', kwargs={'patient_id': self.patient.id})

    def test_create_opd_visit_requires_login(self):
        response = self.client.post(self.url, {'payment_mode': 'CASH'})
        self.assertEqual(response.status_code, 302)

    def test_create_opd_visit_success(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        
        # Create a prior paid visit first to trigger follow-up logic
        OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.COMPLETED
        )
        
        response = self.client.post(self.url, {'payment_mode': 'UPI'})
        
        # Verify visit was created
        visits = OPDVisit.objects.filter(patient=self.patient, visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP)
        self.assertEqual(visits.count(), 1)
        visit = visits.first()
        self.assertEqual(visit.payment_mode, OPDVisit.PaymentModeChoices.UPI)
        self.assertEqual(visit.visit_type, OPDVisit.VisitTypeChoices.FOLLOW_UP)
        self.assertEqual(visit.status, OPDVisit.StatusChoices.WAITING)
        self.assertEqual(visit.created_by, self.user)
        
        # Verify Patient record was NOT duplicated
        self.assertEqual(Patient.objects.filter(mobile_number="9876543222").count(), 1)
        
        # Verify redirect
        self.assertRedirects(response, reverse('receptionist:vitals_entry_detail', kwargs={'patient_id': self.patient.id}))

    def test_create_opd_visit_invalid_payment_mode(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.post(self.url, {'payment_mode': 'INVALID'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OPDVisit.objects.filter(patient=self.patient).count(), 0)


class PatientSummaryViewTest(TestCase):
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
            full_name="Patient One",
            date_of_birth=date(1990, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9876543201",
            address="Test Address One"
        )
        self.patient2 = Patient.objects.create(
            full_name="Patient Two",
            date_of_birth=date(1992, 2, 2),
            gender=Patient.GenderChoices.FEMALE,
            mobile_number="9876543202",
            address="Test Address Two"
        )

    def test_patient_summary_requires_login(self):
        response = self.client.get(reverse('receptionist:patient_summary'))
        self.assertEqual(response.status_code, 302)

    def test_patient_summary_without_id_fallback(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:patient_summary'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['patient'].id, self.patient2.id)

    def test_patient_summary_with_id(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:patient_summary_detail', kwargs={'patient_id': self.patient.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['patient'].id, self.patient.id)

    def test_patient_summary_with_invalid_id(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        import uuid
        response = self.client.get(reverse('receptionist:patient_summary_detail', kwargs={'patient_id': uuid.uuid4()}))
        self.assertEqual(response.status_code, 404)


class EditProfileViewTest(TestCase):
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
            full_name="Patient One",
            date_of_birth=date(1990, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9876543201",
            address="Test Address One"
        )

    def test_edit_profile_requires_login(self):
        response = self.client.get(reverse('receptionist:edit_profile'))
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_get_with_id(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:edit_profile_detail', kwargs={'patient_id': self.patient.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['patient'].id, self.patient.id)

    def test_edit_profile_post_success(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.post(
            reverse('receptionist:edit_profile_detail', kwargs={'patient_id': self.patient.id}),
            {
                'full_name': 'Patient One Updated',
                'date_of_birth': '1990-01-01',
                'gender': Patient.GenderChoices.MALE,
                'mobile_number': '9876543205',
                'address': 'New Address',
                'father_name': 'New Father'
            }
        )
        self.assertRedirects(response, reverse('receptionist:patient_summary_detail', kwargs={'patient_id': self.patient.id}))
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.full_name, 'Patient One Updated')
        self.assertEqual(self.patient.mobile_number, '9876543205')
        self.assertEqual(self.patient.address, 'New Address')
        self.assertEqual(self.patient.father_name, 'New Father')

    def test_edit_profile_post_invalid_mobile(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.post(
            reverse('receptionist:edit_profile_detail', kwargs={'patient_id': self.patient.id}),
            {
                'full_name': 'Patient One Updated',
                'date_of_birth': '1990-01-01',
                'gender': Patient.GenderChoices.MALE,
                'mobile_number': '123',
                'address': 'New Address'
            }
        )
        self.assertEqual(response.status_code, 200)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.full_name, 'Patient One')


class VitalsEntryViewTest(TestCase):
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
            full_name="Vitals Patient",
            date_of_birth=date(1995, 5, 5),
            gender=Patient.GenderChoices.FEMALE,
            mobile_number="9876543209",
            address="Vitals Address"
        )
        self.visit = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.WAITING,
            payment_mode=OPDVisit.PaymentModeChoices.CASH
        )

    def test_vitals_entry_requires_login(self):
        response = self.client.get(reverse('receptionist:vitals_entry'))
        self.assertEqual(response.status_code, 302)

    def test_vitals_entry_get_with_id(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:vitals_entry_detail', kwargs={'patient_id': self.patient.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['patient'].id, self.patient.id)
        self.assertContains(response, "Vitals Patient")
        self.assertContains(response, "Vitals Address")
        self.assertContains(response, "9876543209")
        self.assertContains(response, 'name="blood_group"')

    def test_vitals_entry_post_success(self):
        from receptionist.models import Vitals
        from decimal import Decimal
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.post(
            reverse('receptionist:vitals_entry_detail', kwargs={'patient_id': self.patient.id}),
            {
                'chief_complaint': 'Fever and cold',
                'weight': '15.5',
                'temperature': '38.5',
                'heart_rate': '100',
                'pulse_rate': '98',
                'blood_pressure': '100/70',
                'spo2': '99',
                'blood_group': 'B+'
            }
        )
        self.assertRedirects(response, reverse('receptionist:dashboard'))
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.blood_group, 'B+')
        
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, 'Ready for Doctor')
        
        vitals = Vitals.objects.filter(patient=self.patient).first()
        self.assertIsNotNone(vitals)
        self.assertEqual(vitals.chief_complaint, 'Fever and cold')
        self.assertEqual(vitals.weight, Decimal('15.5'))
        self.assertEqual(vitals.temperature, Decimal('38.5'))
        self.assertEqual(vitals.heart_rate, 100)
        self.assertEqual(vitals.pulse_rate, 98)
        self.assertEqual(vitals.blood_pressure, '100/70')
        self.assertEqual(vitals.spo2, 99)

    def test_edit_latest_vitals_no_vitals(self):
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:edit_latest_vitals', kwargs={'patient_id': self.patient.id}))
        self.assertRedirects(response, reverse('receptionist:patient_summary_detail', kwargs={'patient_id': self.patient.id}))

    def test_edit_latest_vitals_get_success(self):
        from receptionist.models import Vitals
        Vitals.objects.create(
            patient=self.patient,
            visit=self.visit,
            chief_complaint='Old complaint',
            weight='12.5',
            temperature='36.5',
            heart_rate=80,
            pulse_rate=78,
            blood_pressure='120/80',
            spo2=98,
            blood_group='A+'
        )
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:edit_latest_vitals', kwargs={'patient_id': self.patient.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Latest Vitals')
        self.assertContains(response, 'Old complaint')
        self.assertContains(response, '12.5')
        self.assertContains(response, '120/80')

    def test_edit_latest_vitals_post_success(self):
        from receptionist.models import Vitals
        from decimal import Decimal
        vitals = Vitals.objects.create(
            patient=self.patient,
            visit=self.visit,
            chief_complaint='Old complaint',
            weight='12.5',
            temperature='36.5',
            heart_rate=80,
            pulse_rate=78,
            blood_pressure='120/80',
            spo2=98,
            blood_group='A+'
        )
        self.client.login(email="receptionist_test@vatsalyashree.com", password="password123")
        response = self.client.post(
            reverse('receptionist:edit_latest_vitals', kwargs={'patient_id': self.patient.id}),
            {
                'chief_complaint': 'New updated complaint',
                'weight': '14.2',
                'temperature': '37.1',
                'heart_rate': '92',
                'pulse_rate': '90',
                'blood_pressure': '110/70',
                'spo2': '99',
                'blood_group': 'O+'
            }
        )
        self.assertRedirects(response, reverse('receptionist:patient_summary_detail', kwargs={'patient_id': self.patient.id}))
        vitals.refresh_from_db()
        self.assertEqual(vitals.chief_complaint, 'New updated complaint')
        self.assertEqual(vitals.weight, Decimal('14.2'))
        self.assertEqual(vitals.temperature, Decimal('37.1'))
        self.assertEqual(vitals.blood_group, 'O+')
        
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.blood_group, 'O+')
        
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, 'Ready for Doctor')


class DashboardTests(TestCase):
    def setUp(self):
        from accounts.models import User
        from receptionist.models import Patient, OPDVisit
        from django.utils import timezone
        
        self.user = User.objects.create_user(
            email="receptionist_dash@vatsalyashree.com",
            username="receptionist_dash",
            password="password123",
            first_name="Dr. Kalpesh",
            last_name="Patidar",
            role=User.Role.RECEPTIONIST
        )
        self.patient = Patient.objects.create(
            full_name="Aarav Sharma",
            date_of_birth="2020-01-01",
            gender="Male",
            mobile_number="9876543210",
            created_by=self.user,
            updated_by=self.user
        )
        self.visit = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=timezone.localdate(),
            visit_time=timezone.localtime().time(),
            visit_type="New Visit",
            status="Waiting",
            created_by=self.user,
            updated_by=self.user
        )

    def test_dashboard_view_anonymous(self):
        response = self.client.get(reverse('receptionist:dashboard'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('receptionist:dashboard')}")

    def test_dashboard_view_success_empty(self):
        from receptionist.models import Patient, OPDVisit
        OPDVisit.objects.all().delete()
        Patient.objects.all().delete()
        
        self.client.login(email="receptionist_dash@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['today_patients_count'], 0)
        self.assertEqual(response.context['today_new_registrations'], 0)
        self.assertEqual(response.context['today_opd_count'], 0)
        self.assertContains(response, 'No recent patients found.')

    def test_dashboard_view_success_with_data(self):
        from receptionist.models import Patient, OPDVisit
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a patient and visit for yesterday to test percentage changes
        yesterday_patient = Patient.objects.create(
            full_name="Siya Patel",
            date_of_birth="2022-01-01",
            gender="Female",
            mobile_number="9823156094",
            created_by=self.user,
            updated_by=self.user
        )
        OPDVisit.objects.create(
            patient=yesterday_patient,
            visit_date=timezone.localdate() - timedelta(days=1),
            visit_time=timezone.localtime().time(),
            visit_type="New Visit",
            status="Completed",
            created_by=self.user,
            updated_by=self.user
        )
        
        self.client.login(email="receptionist_dash@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Today there is 1 patient visit (self.patient) and 1 yesterday. Percent change should be 0.
        self.assertEqual(response.context['today_patients_count'], 1)
        self.assertEqual(response.context['today_opd_count'], 1)
        self.assertEqual(response.context['patient_percent_change'], 0)
        self.assertEqual(response.context['opd_percent_change'], 0)
        
        # Verify the patient info is in the rendered table
        self.assertContains(response, 'Aarav Sharma')
        self.assertContains(response, 'Waiting')
        self.assertContains(response, '9876543210')

    def test_pending_lab_reports_counter_decreases_when_completed_or_sent(self):
        from lab.models import LaboratoryReport, LabTest
        from django.utils import timezone
        
        # Set visit status to Pending Lab
        self.visit.status = "Pending Lab"
        self.visit.save()
        
        self.client.login(email="receptionist_dash@vatsalyashree.com", password="password123")
        
        # With pending report or status Pending Lab, count should be 1
        res1 = self.client.get(reverse('receptionist:dashboard'))
        self.assertEqual(res1.context['pending_lab_reports'], 1)
        
        # Create a lab test and report with status SENT
        lab_test = LabTest.objects.create(name="CBC Test", price=200)
        report = LaboratoryReport.objects.create(
            patient=self.patient,
            visit=self.visit,
            lab_test=lab_test,
            status='SENT'
        )
        
        # After report status is SENT, pending count should decrease to 0
        res2 = self.client.get(reverse('receptionist:dashboard'))
        self.assertEqual(res2.context['pending_lab_reports'], 0)


class OPDValidityBusinessRulesTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            email="receptionist_rule@vatsalyashree.com",
            username="receptionist_rule",
            password="password123",
            role="RECEPTIONIST"
        )
        self.patient = Patient.objects.create(
            full_name="Rule Patient",
            date_of_birth=date(2000, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9999999999",
            address="Test Address"
        )
        self.hospital = HospitalSettings.objects.create(
            hospital_name="Vatsalya Shree Hospital",
            address="Guna",
            phone_number="123",
            email="test@test.com",
            consultation_fee=350.00,
            opd_validity_days=10,
            free_followups_allowed=1
        )
        self.client.login(email="receptionist_rule@vatsalyashree.com", password="password123")

    def test_opd_validity_cycle(self):
        from datetime import timedelta
        # 1. First Visit: No previous visits, so it must be a New Paid OPD
        url = reverse('receptionist:create_opd_visit', kwargs={'patient_id': self.patient.id})
        response1 = self.client.post(url, {'payment_mode': 'CASH'})
        visit1 = OPDVisit.objects.filter(patient=self.patient).order_by('-created_at').first()
        self.assertEqual(visit1.visit_type, OPDVisit.VisitTypeChoices.NEW_VISIT)
        self.assertRedirects(response1, f"{reverse('receptionist:opd_receipt', kwargs={'patient_id': self.patient.id})}?visit_id={visit1.id}")

        # 2. Second Visit: Within 10 days, should be a Free Follow-up
        response2 = self.client.post(url, {'payment_mode': 'UPI'})
        visit2 = OPDVisit.objects.filter(patient=self.patient).order_by('-created_at').first()
        self.assertEqual(visit2.visit_type, OPDVisit.VisitTypeChoices.FOLLOW_UP)
        self.assertRedirects(response2, reverse('receptionist:vitals_entry_detail', kwargs={'patient_id': self.patient.id}))

        # 3. Third Visit: Still within 10 days, but free follow-up is already used. So it must be a New Paid OPD cycle
        response3 = self.client.post(url, {'payment_mode': 'CASH'})
        visit3 = OPDVisit.objects.filter(patient=self.patient).order_by('-created_at').first()
        self.assertEqual(visit3.visit_type, OPDVisit.VisitTypeChoices.NEW_VISIT)
        self.assertRedirects(response3, f"{reverse('receptionist:opd_receipt', kwargs={'patient_id': self.patient.id})}?visit_id={visit3.id}")

    def test_opd_validity_expiration(self):
        # Create a paid visit that is older than 10 days (e.g. 11 days ago)
        from datetime import timedelta
        old_date = date.today() - timedelta(days=11)
        OPDVisit.objects.create(
            patient=self.patient,
            visit_date=old_date,
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.COMPLETED,
            created_by=self.user,
            updated_by=self.user
        )

        # Since the last paid visit has expired, the next visit must be a New Paid OPD
        url = reverse('receptionist:create_opd_visit', kwargs={'patient_id': self.patient.id})
        response = self.client.post(url, {'payment_mode': 'UPI'})
        visit = OPDVisit.objects.filter(patient=self.patient).order_by('-created_at').first()
        self.assertEqual(visit.visit_type, OPDVisit.VisitTypeChoices.NEW_VISIT)
        self.assertRedirects(response, f"{reverse('receptionist:opd_receipt', kwargs={'patient_id': self.patient.id})}?visit_id={visit.id}")

    def test_followup_workflow_button(self):
        url = reverse('receptionist:create_opd_visit', kwargs={'patient_id': self.patient.id})
        
        # 1. First Follow-up creation should succeed when visit_type is passed in POST
        response = self.client.post(url, {'payment_mode': 'CASH', 'visit_type': 'Follow-up'})
        self.assertEqual(OPDVisit.objects.filter(patient=self.patient, visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP).count(), 1)
        self.assertRedirects(response, reverse('receptionist:patient_list'))
        
        # 2. Subsequent Follow-up creation via this workflow should fail / redirect
        response2 = self.client.post(url, {'payment_mode': 'UPI', 'visit_type': 'Follow-up'})
        self.assertEqual(OPDVisit.objects.filter(patient=self.patient, visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP).count(), 1)
        self.assertRedirects(response2, reverse('receptionist:patient_list'))

    def test_followup_button_annotation(self):
        # Verify the followup_count annotation is correct for patient list
        list_url = reverse('receptionist:patient_list')
        
        # Initially, followup_count should be 0
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        # Find the patient in context
        patient_in_context = None
        for p in response.context['page_obj']:
            if p.id == self.patient.id:
                patient_in_context = p
                break
        self.assertIsNotNone(patient_in_context)
        self.assertEqual(patient_in_context.followup_count, 0)
        
        # Create a Follow-up visit
        OPDVisit.objects.create(
            patient=self.patient,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
            status=OPDVisit.StatusChoices.WAITING
        )
        
        # Now, followup_count should be 1
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        for p in response.context['page_obj']:
            if p.id == self.patient.id:
                patient_in_context = p
                break
        self.assertEqual(patient_in_context.followup_count, 1)

    def test_dashboard_total_opd_excludes_followups(self):
        # Clear existing visits
        OPDVisit.objects.all().delete()
        
        # Create a patient
        patient = Patient.objects.create(
            full_name="Dash Patient",
            date_of_birth=date(2015, 1, 1),
            gender=Patient.GenderChoices.MALE,
            mobile_number="9998887779",
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create 1 "New Visit" and 2 "Follow-up" visits today
        OPDVisit.objects.create(
            patient=patient,
            visit_date=date.today(),
            visit_time="10:00:00",
            visit_type=OPDVisit.VisitTypeChoices.NEW_VISIT,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user,
            updated_by=self.user
        )
        OPDVisit.objects.create(
            patient=patient,
            visit_date=date.today(),
            visit_time="11:00:00",
            visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user,
            updated_by=self.user
        )
        OPDVisit.objects.create(
            patient=patient,
            visit_date=date.today(),
            visit_time="12:00:00",
            visit_type=OPDVisit.VisitTypeChoices.FOLLOW_UP,
            status=OPDVisit.StatusChoices.WAITING,
            created_by=self.user,
            updated_by=self.user
        )

        self.client.login(email="receptionist_rule@vatsalyashree.com", password="password123")
        response = self.client.get(reverse('receptionist:dashboard'))
        self.assertEqual(response.status_code, 200)
        # today_opd_count should count only the New Visit (1), not the Follow-ups
        self.assertEqual(response.context['today_opd_count'], 1)



