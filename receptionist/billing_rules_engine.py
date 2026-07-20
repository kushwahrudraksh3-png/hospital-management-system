"""
IPD Billing Rules Engine (Phase 2)
Determines applicable charge items dynamically based on the patient's admitted Ward.
"""
from .models import IPDChargeMaster


class IPDBillingRulesEngine:
    WARD_CATEGORIES = {
        'General Ward 1': 'General Ward',
        'General Ward 2': 'General Ward',
        'General Ward': 'General Ward',
        'NICU': 'NICU',
        'PICU': 'PICU',
        'ICU': 'ICU',
        'Private Ward': 'Private',
        'Private': 'Private',
        'Deluxe Ward': 'Deluxe',
        'Deluxe': 'Deluxe',
        'Semi Private Ward': 'Semi Private',
        'Semi Private': 'Semi Private',
    }

    @classmethod
    def get_ward_category(cls, ward_type_str):
        if not ward_type_str:
            return 'General Ward'
        w_str = str(ward_type_str).strip()
        w_lower = w_str.lower()
        
        if 'semi' in w_lower:
            return 'Semi Private'
        if 'deluxe' in w_lower:
            return 'Deluxe'
        if w_lower == 'icu':
            return 'ICU'
        if 'picu' in w_lower:
            return 'PICU'
        if 'nicu' in w_lower:
            return 'NICU'
        if 'private' in w_lower:
            return 'Private'
        if 'general' in w_lower:
            return 'General Ward'
            
        return w_str

    @classmethod
    def get_applicable_charges(cls, admission):
        ward_type = getattr(admission, 'ward_type', 'General Ward') or 'General Ward'
        ward_category = cls.get_ward_category(ward_type)

        w_cat_lower = ward_category.lower()
        if w_cat_lower == 'semi private':
            target_wards = ['Semi Private', 'Semi Private Ward']
            fallback_wards = ['Private', 'Private Ward']
        elif w_cat_lower == 'deluxe':
            target_wards = ['Deluxe', 'Deluxe Ward']
            fallback_wards = []
        elif w_cat_lower == 'icu':
            target_wards = ['ICU', 'ICU Ward', 'PICU', 'NICU']
            fallback_wards = []
        elif w_cat_lower == 'picu':
            target_wards = ['PICU', 'PICU Ward', 'ICU']
            fallback_wards = []
        elif w_cat_lower == 'nicu':
            target_wards = ['NICU', 'NICU Ward', 'ICU']
            fallback_wards = []
        elif w_cat_lower == 'private':
            target_wards = ['Private', 'Private Ward']
            fallback_wards = []
        elif w_cat_lower == 'general ward':
            target_wards = ['General Ward', 'General Ward 1', 'General Ward 2', 'General']
            fallback_wards = []
        else:
            target_wards = [ward_category, f"{ward_category} Ward"]
            fallback_wards = ['General Ward']

        # Query ward-specific records first
        qs_specific = IPDChargeMaster.objects.filter(is_active=True, ward__in=target_wards)
        if not qs_specific.exists() and fallback_wards:
            qs_specific = IPDChargeMaster.objects.filter(is_active=True, ward__in=fallback_wards)

        # Query generic All Wards records
        qs_all_wards = IPDChargeMaster.objects.filter(is_active=True, ward='All Wards')

        applicable_charges = []
        seen_names = set()

        # Prioritize ward-specific records over generic All Wards records for deduplication
        for item in list(qs_specific) + list(qs_all_wards):
            item_name = item.name.strip()
            norm_name = item_name.lower()

            if norm_name not in seen_names:
                seen_names.add(norm_name)
                applicable_charges.append({
                    'code': item.code,
                    'name': item.name,
                    'particular': item.name,
                    'charge_type': item.charge_type,
                    'rate': float(item.amount),
                    'unit': item.unit or item.charge_type,
                    'ward': item.ward,
                    'duration': '',
                    'quantity': 1,
                    'amount': 0.00,
                    'is_applicable': True,
                })

        return {
            'admission_id': getattr(admission, 'id', None),
            'ward_type': ward_type,
            'ward_category': ward_category,
            'applicable_charges': applicable_charges,
        }


