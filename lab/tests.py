from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from receptionist.models import Patient, OPDVisit
from .models import LabTest, LaboratoryBill, LaboratoryBillItem
import datetime

User = get_user_model()

class LabBillingWorkflowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="labadmin@vatsalya.com",
            username="labadmin",
            password="password123",
            role="LAB_ADMINISTRATOR",
            first_name="Lab",
            last_name="Admin"
        )
        self.client.login(email="labadmin@vatsalya.com", password="password123")
        
        self.test_cbc = LabTest.objects.create(name="CBC Test", price=250.00, is_active=True)
        self.test_crp = LabTest.objects.create(name="C.R.P. Test", price=250.00, is_active=True)
        
        self.patient = Patient.objects.create(
            full_name="John Doe",
            date_of_birth=datetime.date(2020, 1, 1),
            gender="Male",
            mobile_number="+919876543210",
            address="Test Address"
        )
        self.visit = OPDVisit.objects.create(
            patient=self.patient,
            visit_date=datetime.date.today(),
            visit_time=datetime.time(10, 0),
            visit_type="New Visit",
            status="Pending Lab"
        )

    def test_save_and_print_workflow(self):
        url = reverse('lab:lab_billing')
        data = {
            'visit_id': str(self.visit.id),
            'patient_id': str(self.patient.id),
            'tests': [str(self.test_cbc.id), str(self.test_crp.id)]
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        bill = LaboratoryBill.objects.get(visit=self.visit)
        self.assertIn(reverse('lab:bill_receipt'), response.url)
        self.assertIn(str(bill.id), response.url)
        
        self.assertEqual(bill.grand_total, 500.00)
        self.assertEqual(bill.items.count(), 2)
        self.assertTrue(bill.bill_number.startswith("LB-"))
        
        receipt_url = f"{reverse('lab:bill_receipt')}?bill_id={bill.id}"
        receipt_response = self.client.get(receipt_url)
        self.assertEqual(receipt_response.status_code, 200)
        self.assertContains(receipt_response, "John Doe")
        self.assertContains(receipt_response, "CBC Test")
        self.assertContains(receipt_response, "C.R.P. Test")
        self.assertContains(receipt_response, "500.00")
        
    def test_no_duplicate_bills(self):
        bill = LaboratoryBill.objects.create(visit=self.visit, patient=self.patient, grand_total=100.00)
        item = LaboratoryBillItem.objects.create(bill=bill, test=self.test_cbc, name=self.test_cbc.name, price=self.test_cbc.price)
        
        url = reverse('lab:lab_billing')
        data = {
            'visit_id': str(self.visit.id),
            'patient_id': str(self.patient.id),
            'tests': [str(self.test_crp.id)]
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(LaboratoryBill.objects.filter(visit=self.visit).count(), 1)
        
        bill.refresh_from_db()
        self.assertEqual(bill.grand_total, 250.00)
        self.assertEqual(bill.items.count(), 1)
        self.assertEqual(bill.items.first().test, self.test_crp)

    def test_report_entry_queue_and_form(self):
        # 1. Access the queue page. Initially, there are no bills.
        url = reverse('lab:report_entry')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Should not display our patient John Doe yet since billing is not completed
        self.assertNotContains(response, "John Doe")
        self.assertContains(response, "No pending laboratory requests.")

        # 2. Create a bill to complete laboratory billing for this visit/patient
        bill = LaboratoryBill.objects.create(
            visit=self.visit,
            patient=self.patient,
            grand_total=500.00
        )
        LaboratoryBillItem.objects.create(
            bill=bill,
            test=self.test_cbc,
            name=self.test_cbc.name,
            price=self.test_cbc.price
        )

        # 3. Access the queue page again. The patient should now appear.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "LB-") # Bill number pattern
        self.assertContains(response, "Create Report")
        
        # Verify the "Create Report" button URL points to the correct patient, visit, and lab test
        expected_btn_url = f"{reverse('lab:report_entry')}?visit_id={self.visit.id}&patient_id={self.patient.id}&bill_id={bill.id}&lab_test_id={self.test_cbc.id}"
        self.assertContains(response, expected_btn_url)

        # 4. Access the report entry form directly by passing parameters.
        form_url = f"{reverse('lab:report_entry')}?visit_id={self.visit.id}&patient_id={self.patient.id}&bill_id={bill.id}&lab_test_id={self.test_cbc.id}"
        form_response = self.client.get(form_url)
        self.assertEqual(form_response.status_code, 200)
        # Patient details should render dynamically
        self.assertContains(form_response, "John Doe")
        self.assertContains(form_response, self.patient.uhid)
        # Check standard references in form mode
        self.assertContains(form_response, "CBC Test Parameter Entry")

    def test_xray_billing_workflow(self):
        # 1. Access doctor prescription page and check that "Generate X-Ray Bill" button is present
        prescription_url = f"{reverse('lab:doctor_prescription')}?visit_id={self.visit.id}&patient_id={self.patient.id}"
        response = self.client.get(prescription_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Generate X-Ray Bill")
        
        # 2. Click "Generate X-Ray Bill" which hits views.xray_bill_generate
        generate_url = f"{reverse('lab:xray_bill_generate')}?visit_id={self.visit.id}&patient_id={self.patient.id}"
        response = self.client.get(generate_url)
        # Should redirect to xray bill receipt
        bill = LaboratoryBill.objects.get(visit=self.visit)
        self.assertRedirects(response, f"{reverse('lab:xray_bill_receipt')}?bill_id={bill.id}")
        
        # Check that X-Ray test is in the bill
        self.assertEqual(bill.items.count(), 1)
        self.assertEqual(bill.items.first().name, "X-Ray (Per Film)")
        self.assertEqual(bill.grand_total, 400.00)
        
        # 3. Access xray bill receipt page
        receipt_url = f"{reverse('lab:xray_bill_receipt')}?bill_id={bill.id}"
        receipt_response = self.client.get(receipt_url)
        self.assertEqual(receipt_response.status_code, 200)
        
        # Verify patient details, date, and investigation info are auto-filled
        self.assertContains(receipt_response, self.patient.full_name)
        self.assertContains(receipt_response, "X-Ray (Per Film)")
        self.assertContains(receipt_response, "400.00")
        self.assertContains(receipt_response, "Print X-Ray Receipt")

