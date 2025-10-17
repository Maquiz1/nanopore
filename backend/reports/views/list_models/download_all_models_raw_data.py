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
class ExportAllModelsRawDataView(View):
    """
    Export raw data from all models in the 'nanopore' app to separate CSV files.
    Each model gets its own CSV file.
    """

    exclude_fields = [
        'id', 'pid1', 'pid2', 'created_at', 'updated_at', 'created_by', 'updated_by', 'remarks',
        'enrollment', 'clinic_laboratory', 'zonal_laboratory', 'diagnosis', 'regimen_changes'
    ]

    def get(self, request):
        # Prepare response as a zip archive (optional) or just CSV for demo
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_models_data.csv"'
        writer = csv.writer(response)

        # Loop through all models in 'nanopore' app
        for model in apps.get_app_config('nanopore').get_models():
            model_name = model.__name__

            # Write model name as a header
            writer.writerow([f"--- {model_name} ---"])

            # Determine fields to export
            fields = []
            header = []

            for f in model._meta.get_fields():
                if f.name in self.exclude_fields:
                    continue
                if model_name == 'RegimenChanges' and f.name == 'screening':
                    continue
                fields.append(f)
                # Column name logic
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
                    try:
                        # ManyToMany → list of IDs separated by ;
                        if f.many_to_many:
                            value = getattr(obj, f.name).all()
                            row.append(';'.join(str(v.pk) for v in value))
                        # OneToOne to Screening → pid
                        elif f.one_to_one and f.related_model.__name__ == 'Screening':
                            value = getattr(obj, f.name, None)
                            row.append(value.pid if value else '')
                        # Other ForeignKeys → ID
                        elif f.many_to_one or f.one_to_one:
                            value = getattr(obj, f.name, None)
                            row.append(value.pk if value else '')
                        # Regular fields
                        else:
                            value = getattr(obj, f.name)
                            row.append(value)
                    except (AttributeError, f.related_model.DoesNotExist):
                        row.append('')
                # Add remarks
                remarks_value = getattr(obj, 'remarks', '')
                row.append(remarks_value if remarks_value else '')
                writer.writerow(row)

            # Add empty line between models
            writer.writerow([])

        return response
