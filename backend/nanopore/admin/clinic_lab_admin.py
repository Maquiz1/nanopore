from django.contrib import admin
from nanopore.models.clinic_lab import ClinicLaboratory

@admin.register(ClinicLaboratory)
class ClinicLaboratoryAdmin(admin.ModelAdmin):
    list_display = ('screening_pid', 'created_at')
    # list_filter = ('test_date',)
    # search_fields = ('screening__pid')

    def screening_pid(self, obj):
        return obj.screening.pid
    screening_pid.short_description = 'PID'
