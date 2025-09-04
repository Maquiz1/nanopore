from django.contrib import admin
from nanopore.models.enrollment import Enrollment

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('screening_pid', 'enrollment_date', 'created_at')
    list_filter = ('enrollment_date',)
    search_fields = ('screening__pid',)

    def screening_pid(self, obj):
        return obj.screening.pid
    screening_pid.short_description = 'PID'
