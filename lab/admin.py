from django.contrib import admin
from .models import LabTest, LaboratoryBill, LaboratoryBillItem, LabTestParameter, LaboratoryReport, LaboratoryReportResult

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)

class LaboratoryBillItemInline(admin.TabularInline):
    model = LaboratoryBillItem
    extra = 0
    raw_id_fields = ("test",)

@admin.register(LaboratoryBill)
class LaboratoryBillAdmin(admin.ModelAdmin):
    list_display = ("bill_number", "patient", "visit", "grand_total", "bill_date", "bill_time")
    list_filter = ("bill_date",)
    search_fields = ("bill_number", "patient__full_name", "patient__uhid")
    inlines = [LaboratoryBillItemInline]


@admin.register(LabTestParameter)
class LabTestParameterAdmin(admin.ModelAdmin):
    list_display = ("get_test_name", "parameter_name", "unit", "male_reference_range", "female_reference_range", "common_reference_range", "parameter_type", "display_order", "is_active")
    list_filter = ("lab_test", "is_active")
    search_fields = ("lab_test__name", "parameter_name")
    ordering = ("display_order", "parameter_name")
    list_select_related = ("lab_test",)

    def get_test_name(self, obj):
        return obj.lab_test.name
    get_test_name.short_description = "Test Name"
    get_test_name.admin_order_field = "lab_test__name"


class LaboratoryReportResultInline(admin.TabularInline):
    model = LaboratoryReportResult
    extra = 0

@admin.register(LaboratoryReport)
class LaboratoryReportAdmin(admin.ModelAdmin):
    list_display = ("report_number", "patient", "visit", "lab_test", "generated_date", "generated_by")
    list_filter = ("generated_date", "lab_test")
    search_fields = ("report_number", "patient__full_name", "patient__uhid")
    inlines = [LaboratoryReportResultInline]


