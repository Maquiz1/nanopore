from django.contrib import admin
from nanopore.models.zonal_lab import ZonalLaboratory

@admin.register(ZonalLaboratory)
class ZonalLaboratoryAdmin(admin.ModelAdmin):
    list_display = ('screening_pid', 'created_at')
    # list_filter = ('test_date',)
    # search_fields = ('screening__pid', 'test_name')

    def screening_pid(self, obj):
        return obj.screening.pid
    screening_pid.short_description = 'PID'
