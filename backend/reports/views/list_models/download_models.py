from django.views import View
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.apps import apps
import csv

# Decorator for staff-only access
def staff_required(view_func):
    return method_decorator(staff_member_required, name='dispatch')(view_func)

# @staff_required
class ExportModelRawDataView(View):
    """
    Export raw model data to CSV.
    - Includes only actual model fields (no M2M or related names).
    - ForeignKeys are exported as IDs (raw values).
    - Excludes system/meta fields (e.g. created_at, updated_by).
    """

    exclude_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get(self, request, model_name):
        try:
            model = apps.get_model('nanopore', model_name)  # change app name if needed
        except LookupError:
            return HttpResponse("Unknown model", status=404)

        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_raw_data.csv"'
        writer = csv.writer(response)

        # Get model fields (only concrete fields, exclude auto-created)
        fields = [
            f for f in model._meta.get_fields()
            if f.concrete and not f.auto_created and f.name not in self.exclude_fields
        ]

        # Write header row
        writer.writerow([f.name for f in fields])

        # Write data rows
        for obj in model.objects.all():
            row = []
            for f in fields:
                value = getattr(obj, f.name)
                # For FK/OneToOne fields, export the raw ID (PK)
                if f.many_to_one or f.one_to_one:
                    row.append(value.pk if value else '')
                else:
                    row.append(value)
            writer.writerow(row)

        return response
