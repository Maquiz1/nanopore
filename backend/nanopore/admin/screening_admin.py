from django.contrib import admin
from nanopore.models.screening import Screening
from nanopore.models.enrollment import Enrollment


class EnrollmentInline(admin.StackedInline):
    model = Enrollment
    extra = 0
    fields = ('enrollment_date', 'remarks', 'created_by', 'updated_by')
    readonly_fields = ('created_by', 'updated_by')
    can_delete = True


@admin.register(Screening)
class ScreeningAdmin(admin.ModelAdmin):
    list_display = ('pid', 'site_name', 'age', 'sex_name', 'eligible_value', 'created_at')
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
        return obj.eligible
    eligible_value.boolean = True        # ✅ shows checkmark in admin
    eligible_value.short_description = 'Eligible'
