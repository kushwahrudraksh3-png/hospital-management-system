"""
Seed script for Final Hospital Rate Master
Populates standard charge rates for General Ward, NICU, PICU, Private, and Deluxe wards.
Prevents duplicates using get_or_create.
"""

SEED_RATES = [
    # GENERAL WARD
    ('GEN_REG', 'General Ward', 'Registration', 'One Time', 100.00, 'One Time'),
    ('GEN_OXYGEN_HR', 'General Ward', 'Oxygen', 'Per Hour', 100.00, 'Per Hour'),
    ('GEN_SERVICE', 'General Ward', 'Service Charge', 'Per Day', 200.00, 'Per Day'),
    ('GEN_DOC_FEE', 'General Ward', 'Hospital Doctor Fee', 'Per Day', 800.00, 'Per Day'),
    ('GEN_NURSING', 'General Ward', 'Nursing Charge', 'Per Day', 400.00, 'Per Day'),
    ('GEN_BMW', 'General Ward', 'Biomedical Waste', 'Per Day', 100.00, 'Per Day'),
    ('GEN_PULSE_OXY', 'General Ward', 'Pulse Oxy / Multipara', 'Per Day', 500.00, 'Per Day'),
    ('GEN_SYRINGE_PUMP', 'General Ward', 'Syringe Pump', 'Per Day', 300.00, 'Per Day'),
    ('GEN_RBS', 'General Ward', 'RBS', 'One Time', 50.00, 'One Time'),
    ('GEN_HFNC', 'General Ward', 'HFNC', 'Per Day', 1000.00, 'Per Day'),
    ('GEN_VENTILATOR', 'General Ward', 'Ventilator', 'Per Day', 2000.00, 'Per Day'),
    ('GEN_NEBULIZER', 'General Ward', 'Nebulizer Charges', 'Per Use', 100.00, 'Per Use'),
    ('GEN_EMERGENCY', 'General Ward', 'Emergency Charges', 'One Time', 500.00, 'One Time'),

    # NICU
    ('NICU_REG', 'NICU', 'Registration', 'One Time', 100.00, 'One Time'),
    ('NICU_OXYGEN', 'NICU', 'Oxygen', 'Per Day', 600.00, 'Per Day'),
    ('NICU_PHOTO', 'NICU', 'Phototherapy', 'Per Hour', 100.00, 'Per Hour'),
    ('NICU_SERVICE', 'NICU', 'Service Charge', 'Per Day', 200.00, 'Per Day'),
    ('NICU_WARMER', 'NICU', 'Warmer', 'Per Day', 1000.00, 'Per Day'),
    ('NICU_DOC_FEE', 'NICU', 'Hospital Doctor Fee', 'Per Day', 1000.00, 'Per Day'),
    ('NICU_BED', 'NICU', 'Bed Charge NICU', 'Per Day', 1000.00, 'Per Day'),
    ('NICU_NURSING', 'NICU', 'Nursing Charge', 'Per Day', 400.00, 'Per Day'),
    ('NICU_BMW', 'NICU', 'Biomedical Waste', 'Per Day', 100.00, 'Per Day'),
    ('NICU_PULSE_OXY', 'NICU', 'Pulse Oxy / Multipara', 'Per Day', 500.00, 'Per Day'),
    ('NICU_SYRINGE_PUMP', 'NICU', 'Syringe Pump', 'Per Day', 300.00, 'Per Day'),
    ('NICU_AC', 'NICU', 'A/C Charge', 'Per Day', 250.00, 'Per Day'),
    ('NICU_RBS', 'NICU', 'RBS', 'One Time', 50.00, 'One Time'),
    ('NICU_HFNC', 'NICU', 'HFNC', 'Per Day', 1000.00, 'Per Day'),
    ('NICU_VENTILATOR', 'NICU', 'Ventilator', 'Per Day', 2000.00, 'Per Day'),
    ('NICU_NEBULIZER', 'NICU', 'Nebulizer Charges', 'Per Use', 100.00, 'Per Use'),
    ('NICU_EMERGENCY', 'NICU', 'Emergency Charges', 'One Time', 500.00, 'One Time'),

    # PICU
    ('PICU_REG', 'PICU', 'Registration', 'One Time', 100.00, 'One Time'),
    ('PICU_OXYGEN', 'PICU', 'Oxygen', 'Per Day', 600.00, 'Per Day'),
    ('PICU_PHOTO', 'PICU', 'Phototherapy', 'Per Hour', 100.00, 'Per Hour'),
    ('PICU_SERVICE', 'PICU', 'Service Charge', 'Per Day', 200.00, 'Per Day'),
    ('PICU_WARMER', 'PICU', 'Warmer', 'Per Day', 1000.00, 'Per Day'),
    ('PICU_DOC_FEE', 'PICU', 'Hospital Doctor Fee', 'Per Day', 1000.00, 'Per Day'),
    ('PICU_BED', 'PICU', 'Bed Charge PICU', 'Per Day', 1000.00, 'Per Day'),
    ('PICU_NURSING', 'PICU', 'Nursing Charge', 'Per Day', 400.00, 'Per Day'),
    ('PICU_BMW', 'PICU', 'Biomedical Waste', 'Per Day', 100.00, 'Per Day'),
    ('PICU_PULSE_OXY', 'PICU', 'Pulse Oxy / Multipara', 'Per Day', 500.00, 'Per Day'),
    ('PICU_SYRINGE_PUMP', 'PICU', 'Syringe Pump', 'Per Day', 300.00, 'Per Day'),
    ('PICU_AC', 'PICU', 'A/C Charge', 'Per Day', 250.00, 'Per Day'),
    ('PICU_RBS', 'PICU', 'RBS', 'One Time', 50.00, 'One Time'),
    ('PICU_HFNC', 'PICU', 'HFNC', 'Per Day', 1000.00, 'Per Day'),
    ('PICU_VENTILATOR', 'PICU', 'Ventilator', 'Per Day', 2000.00, 'Per Day'),
    ('PICU_NEBULIZER', 'PICU', 'Nebulizer Charges', 'Per Use', 100.00, 'Per Use'),
    ('PICU_EMERGENCY', 'PICU', 'Emergency Charges', 'One Time', 500.00, 'One Time'),

    # PRIVATE
    ('PRI_REG', 'Private', 'Registration', 'One Time', 100.00, 'One Time'),
    ('PRI_OXYGEN_HR', 'Private', 'Oxygen', 'Per Hour', 100.00, 'Per Hour'),
    ('PRI_PHOTO', 'Private', 'Phototherapy', 'Per Hour', 100.00, 'Per Hour'),
    ('PRI_SERVICE', 'Private', 'Service Charge', 'Per Day', 200.00, 'Per Day'),
    ('PRI_WARMER', 'Private', 'Warmer', 'Per Day', 1000.00, 'Per Day'),
    ('PRI_DOC_FEE', 'Private', 'Hospital Doctor Fee', 'Per Day', 1000.00, 'Per Day'),
    ('PRI_BED', 'Private', 'Bed Charge Private Ward', 'Per Day', 1200.00, 'Per Day'),
    ('PRI_NURSING', 'Private', 'Nursing Charge', 'Per Day', 400.00, 'Per Day'),
    ('PRI_BMW', 'Private', 'Biomedical Waste', 'Per Day', 100.00, 'Per Day'),
    ('PRI_PULSE_OXY', 'Private', 'Pulse Oxy / Multipara', 'Per Day', 500.00, 'Per Day'),
    ('PRI_SYRINGE_PUMP', 'Private', 'Syringe Pump', 'Per Day', 300.00, 'Per Day'),
    ('PRI_AC', 'Private', 'A/C Charge', 'Per Day', 800.00, 'Per Day'),
    ('PRI_RBS', 'Private', 'RBS', 'One Time', 50.00, 'One Time'),
    ('PRI_HFNC', 'Private', 'HFNC', 'Per Day', 1000.00, 'Per Day'),
    ('PRI_VENTILATOR', 'Private', 'Ventilator', 'Per Day', 2000.00, 'Per Day'),
    ('PRI_NEBULIZER', 'Private', 'Nebulizer Charges', 'Per Use', 100.00, 'Per Use'),
    ('PRI_EMERGENCY', 'Private', 'Emergency Charges', 'One Time', 500.00, 'One Time'),

    # DELUXE
    ('DEL_REG', 'Deluxe', 'Registration', 'One Time', 100.00, 'One Time'),
    ('DEL_OXYGEN_HR', 'Deluxe', 'Oxygen', 'Per Hour', 100.00, 'Per Hour'),
    ('DEL_SERVICE', 'Deluxe', 'Service Charge', 'Per Day', 200.00, 'Per Day'),
    ('DEL_WARMER', 'Deluxe', 'Warmer', 'Per Day', 1000.00, 'Per Day'),
    ('DEL_DOC_FEE', 'Deluxe', 'Hospital Doctor Fee', 'Per Day', 1000.00, 'Per Day'),
    ('DEL_BED', 'Deluxe', 'Bed Charge Deluxe Ward', 'Per Day', 2000.00, 'Per Day'),
    ('DEL_NURSING', 'Deluxe', 'Nursing Charge', 'Per Day', 400.00, 'Per Day'),
    ('DEL_BMW', 'Deluxe', 'Biomedical Waste', 'Per Day', 100.00, 'Per Day'),
    ('DEL_PULSE_OXY', 'Deluxe', 'Pulse Oxy / Multipara', 'Per Day', 500.00, 'Per Day'),
    ('DEL_SYRINGE_PUMP', 'Deluxe', 'Syringe Pump', 'Per Day', 300.00, 'Per Day'),
    ('DEL_AC', 'Deluxe', 'A/C Charge', 'Per Day', 800.00, 'Per Day'),
    ('DEL_RBS', 'Deluxe', 'RBS', 'One Time', 50.00, 'One Time'),
    ('DEL_HFNC', 'Deluxe', 'HFNC', 'Per Day', 1000.00, 'Per Day'),
    ('DEL_VENTILATOR', 'Deluxe', 'Ventilator', 'Per Day', 2000.00, 'Per Day'),
    ('DEL_NEBULIZER', 'Deluxe', 'Nebulizer Charges', 'Per Use', 100.00, 'Per Use'),
    ('DEL_EMERGENCY', 'Deluxe', 'Emergency Charges', 'One Time', 500.00, 'One Time'),

    # ALL WARDS / GENERAL FALLBACK
    ('NEBULIZER', 'All Wards', 'Nebulizer Charges', 'Per Use', 100.00, 'Per Use'),
    ('EMERGENCY', 'All Wards', 'Emergency Charges', 'One Time', 500.00, 'One Time'),
]


def seed_hospital_rate_master():
    from .models import IPDChargeMaster
    created_count = 0
    updated_count = 0

    # Ensure removed duplicate/obsolete codes are marked inactive
    IPDChargeMaster.objects.filter(code__in=['GEN_BED', 'GEN_OXYGEN_DAY', 'PRI_OXYGEN_DAY', 'DEL_OXYGEN_DAY']).update(is_active=False)

    for code, ward, name, c_type, amount, unit in SEED_RATES:
        obj, created = IPDChargeMaster.objects.get_or_create(
            code=code,
            defaults={
                'ward': ward,
                'name': name,
                'charge_type': c_type,
                'amount': amount,
                'unit': unit,
                'is_active': True,
            }
        )
        if created:
            created_count += 1
        else:
            # Update ward/unit/name attributes if record pre-existed from earlier migrations
            obj.ward = ward
            obj.name = name
            obj.unit = unit
            obj.is_active = True
            obj.save(update_fields=['ward', 'name', 'unit', 'is_active'])
            updated_count += 1

    return created_count, updated_count

