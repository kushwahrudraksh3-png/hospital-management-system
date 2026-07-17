from django.apps import AppConfig


class LabConfig(AppConfig):
    name = 'lab'

    def ready(self):
        import sys
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            return
        try:
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
            for name, price in TEST_DATA:
                LabTest.objects.get_or_create(name=name, defaults={"price": price, "is_active": True})
        except Exception:
            pass
