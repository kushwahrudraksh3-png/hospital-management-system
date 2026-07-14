from django.contrib import admin
from .models import Patient, OPDVisit, HospitalSettings, Vitals


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

