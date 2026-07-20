from django.apps import AppConfig


class ReceptionistConfig(AppConfig):
    name = 'receptionist'

    def ready(self):
        try:
            from .rate_master_seed import seed_hospital_rate_master
            seed_hospital_rate_master()
        except Exception:
            pass
