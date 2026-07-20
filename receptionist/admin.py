from django.contrib import admin
from .models import Patient, OPDVisit, HospitalSettings, Vitals, IPDAdmission, WardMaster, RoomMaster, BedMaster, IPDChargeMaster, IPDBill, IPDBillItem


class IPDBillItemInline(admin.TabularInline):
    model = IPDBillItem
    extra = 0
    fields = ('display_order', 'particular', 'duration', 'unit', 'rate', 'quantity', 'amount')


@admin.register(IPDBill)
class IPDBillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'patient', 'admission', 'gross_total', 'discount', 'deposit_received', 'net_amount', 'balance_due', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('bill_number', 'patient__full_name', 'patient__uhid', 'admission__admission_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [IPDBillItemInline]


@admin.register(WardMaster)
class WardMasterAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(RoomMaster)
class RoomMasterAdmin(admin.ModelAdmin):
    list_display = ("room_number", "ward", "room_type", "capacity")
    list_filter = ("ward", "room_type")
    search_fields = ("room_number", "ward__name")


@admin.register(BedMaster)
class BedMasterAdmin(admin.ModelAdmin):
    list_display = ("bed_number", "room", "is_occupied")
    list_filter = ("room__ward", "is_occupied")
    search_fields = ("bed_number", "room__room_number")


@admin.register(IPDChargeMaster)
class IPDChargeMasterAdmin(admin.ModelAdmin):
    list_display = ("ward", "name", "charge_type", "amount", "unit", "is_active", "code")
    list_filter = ("ward", "charge_type", "is_active")
    search_fields = ("code", "name", "ward")
    list_editable = ("amount", "charge_type", "is_active")



@admin.register(IPDAdmission)
class IPDAdmissionAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "visit",
        "admission_date",
        "admission_time",
        "admitting_doctor",
        "ward_type",
        "room_number",
        "bed_number",
        "created_at",
    )
    search_fields = (
        "patient__full_name",
        "patient__uhid",
        "visit__opd_number",
    )
    list_filter = (
        "ward_type",
        "admission_date",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )



@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "uhid",
        "full_name",
        "gender",
        "date_of_birth",
        "age_display",
        "mobile_number",
        "is_active",
        "created_at",
    )
    search_fields = (
        "uhid",
        "full_name",
        "mobile_number",
    )
    list_filter = (
        "gender",
        "is_active",
        "created_at",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "uhid",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    def age_display(self, obj):
        return obj.age
    age_display.short_description = "Age"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OPDVisit)
class OPDVisitAdmin(admin.ModelAdmin):
    list_display = (
        "opd_number",
        "patient",
        "visit_date",
        "visit_time",
        "visit_type",
        "token_number",
        "status",
        "created_at",
    )
    search_fields = (
        "opd_number",
        "patient__full_name",
        "patient__uhid",
    )
    list_filter = (
        "visit_type",
        "status",
        "visit_date",
    )
    ordering = ("-visit_date", "-visit_time")
    readonly_fields = (
        "opd_number",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HospitalSettings)
class HospitalSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "hospital_name",
        "phone_number",
        "email",
        "consultation_fee",
        "updated_at",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Vitals)
class VitalsAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "visit",
        "chief_complaint",
        "weight",
        "temperature",
        "heart_rate",
        "pulse_rate",
        "blood_pressure",
        "spo2",
        "blood_group",
        "created_at",
    )
    search_fields = (
        "patient__full_name",
        "patient__uhid",
        "visit__opd_number",
        "chief_complaint",
    )
    list_filter = (
        "blood_group",
        "created_at",
    )
    readonly_fields = (
        "created_at",
        "created_by",
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

