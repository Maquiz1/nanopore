from django.contrib import admin
from nanopore.models.clinic_lab import ClinicLaboratory
from simple_history.admin import SimpleHistoryAdmin
from nanopore.models.clinic_lab import HistoricalClinicLaboratory

# @admin.register(ClinicLaboratory)
# class ClinicLaboratoryAdmin(admin.ModelAdmin):
#     list_display = ('screening_pid', 'created_at')
#     # list_filter = ('test_date',)
#     # search_fields = ('screening__pid')

#     def screening_pid(self, obj):
#         return obj.screening.pid
#     screening_pid.short_description = 'PID'


@admin.register(ClinicLaboratory)
class ClinicLaboratoryAdmin(SimpleHistoryAdmin):

    list_display = ('screening_pid', 'created_at')
    # list_filter = ('test_date',)
    # search_fields = ('screening__pid',)

    def screening_pid(self, obj):
        return obj.screening.pid
    screening_pid.short_description = 'PID'
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    
@admin.register(HistoricalClinicLaboratory)
class HistoricalClinicLaboratoryAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'history_date',
        'history_user',
        'history_type',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
