from django.contrib import admin
from .models import Screening, Enrollment


class EnrollmentInline(admin.StackedInline):
    model = Enrollment
    extra = 0
    fields = ('enrollment_date', 'remarks', 'created_by', 'updated_by')
    readonly_fields = ('created_by', 'updated_by')
    can_delete = True


@admin.register(Screening)
class ScreeningAdmin(admin.ModelAdmin):
    list_display = ('pid', 'site_name', 'age', 'sex_name', 'eligible_value', 'created_at')
    # Filters only on actual fields of Screening
    list_filter = ('site', 'eligible', 'screening_date')
    search_fields = ('pid', 'pid1', 'pid2')
    date_hierarchy = 'screening_date'
    inlines = [EnrollmentInline]

    def site_name(self, obj):
        return obj.site.name if obj.site else 'N/A'
    site_name.short_description = 'Site'

    def sex_name(self, obj):
        return obj.sex.name if obj.sex else 'N/A'
    sex_name.short_description = 'Sex'

    def eligible_value(self, obj):
        return obj.eligible.value if obj.eligible else 'N/A'
    eligible_value.short_description = 'Eligible'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('screening_pid', 'enrollment_date', 'created_at')
    # Filters only on actual Enrollment fields
    list_filter = ('enrollment_date',)
    search_fields = ('screening__pid',)

    def screening_pid(self, obj):
        return obj.screening.pid
    screening_pid.short_description = 'PID'
