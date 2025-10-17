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
    - ForeignKeys exported as IDs.
    - Excludes system/meta fields.
    - Replaces 'remarks' column with 'model_name' column.
    """

    exclude_fields = [
        'pid1', 'created_at', 'updated_at', 'created_by', 'updated_by', 'remarks'
    ]

    def get(self, request, model_name):
        try:
            model = apps.get_model('nanopore', model_name)
        except LookupError:
            return HttpResponse("Unknown model", status=404)

        # Prepare response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_raw_data.csv"'
        writer = csv.writer(response)

        # Get model fields (exclude unwanted)
        fields = [
            f for f in model._meta.get_fields()
            if f.concrete and not f.auto_created and f.name not in self.exclude_fields
        ]

        # Replace 'remarks' with 'model_name' in header
        header = [f.name for f in fields] + ['model_name']
        writer.writerow(header)

        # Write data rows
        for obj in model.objects.all():
            row = []
            for f in fields:
                value = getattr(obj, f.name)
                if f.many_to_one or f.one_to_one:
                    row.append(value.pk if value else '')
                else:
                    row.append(value)

            # Add 'model_name' column
            row.append(model_name)
            writer.writerow(row)

        return response
