from django.views import View
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.apps import apps
import csv


# Decorator for staff-only access
def staff_required(view_func):
    return method_decorator(staff_member_required, name='dispatch')(view_func)


@staff_required
class ExportModelRawDataView(View):
    """
    Export raw model data to CSV.
    - Includes only real database fields (no M2M or related names).
    - Exports ForeignKeys as raw IDs.
    - Excludes system/meta fields.
    - Renames the 'remarks' field to '<model_name>_remarks'.
    - For OneToOneField to Screening, export Screening.pid instead of the relation,
      and column name becomes 'pid'.
    - Exclude screening field entirely for RegimeChanges model.
    """

    exclude_fields = [
        'pid1', 'pid2', 'created_at', 'updated_at', 'created_by', 'updated_by', 'remarks'
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

        # Determine fields to export
        fields = []
        header = []
        for f in model._meta.get_fields():
            if f.concrete and not f.auto_created and f.name not in self.exclude_fields:
                # Skip screening for RegimenChanges
                if model_name == 'RegimenChanges' and f.name == 'screening':
                    continue
                fields.append(f)

                # Column name: 'pid' if it's OneToOne to Screening
                if f.one_to_one and f.related_model.__name__ == 'Screening':
                    header.append('pid')
                else:
                    header.append(f.name)

        # Add remarks column
        remarks_field_name = f"{model_name.lower()}_remarks"
        header.append(remarks_field_name)
        writer.writerow(header)

        # Write data rows
        for obj in model.objects.all():
            row = []
            for f in fields:
                value = getattr(obj, f.name)

                # If this field is OneToOne to Screening → export pid
                if f.one_to_one and f.related_model.__name__ == 'Screening':
                    row.append(value.pid if value else '')
                # For other ForeignKeys → export ID
                elif f.many_to_one or f.one_to_one:
                    row.append(value.pk if value else '')
                else:
                    row.append(value)

            # Add <model_name>_remarks column
            remarks_value = getattr(obj, 'remarks', '')
            row.append(remarks_value if remarks_value else '')

            writer.writerow(row)

        return response
