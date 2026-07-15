from django.contrib import admin
from django.utils.html import format_html
from .models import Prescription


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("patient", "visit", "doctor", "created_at", "view_file_link")
    list_filter = ("created_at", "doctor")
    search_fields = ("patient__full_name", "visit__opd_number")

    def view_file_link(self, obj):
        if obj.image:
            return format_html('<a href="{}" target="_blank">Download/View Prescription</a>', obj.image.url)
        return "No File"
    view_file_link.short_description = "Final Prescription File"
