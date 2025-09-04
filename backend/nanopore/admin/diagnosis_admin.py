from django.contrib import admin
from nanopore.models.diagnosis import Diagnosis

@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('screening_pid', 'diagnosis_name', 'diagnosis_date', 'created_at')
    list_filter = ('diagnosis_date',)
    search_fields = ('screening__pid', 'diagnosis_name')

    def screening_pid(self, obj):
        return obj.screening.pid
    screening_pid.short_description = 'PID'
