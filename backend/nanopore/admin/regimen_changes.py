from django.contrib import admin
from nanopore.models.regimen_changes import RegimenChanges

@admin.register(RegimenChanges)
class RegimenChangesAdmin(admin.ModelAdmin):
    list_display = ('screening_pid', 'drug', 'date', 'changes', 'reason', 'created_at')
    list_filter = ('date', 'changes', 'reason')
    search_fields = ('screening__pid', 'drug')

    def screening_pid(self, obj):
        return obj.screening.pid
    screening_pid.short_description = 'PID'
