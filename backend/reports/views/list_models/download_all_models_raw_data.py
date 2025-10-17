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
class ExportAllModelsRawDataView(View):
    """
    Export all models' data into a single CSV aligned by Screening.pid.
    PID is the first column. Models are mapped via their Screening relation.
    If no related object exists for a Screening, columns are empty.
    """

    exclude_fields = [
        'id', 'pid1', 'pid2', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'enrollment', 'clinic_laboratory', 'zonal_laboratory', 'diagnosis', 'regimen_changes'
    ]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_models_by_screening.csv"'
        writer = csv.writer(response)

        # Get all Screening objects
        Screening = apps.get_model('nanopore', 'Screening')
        screening_list = list(Screening.objects.all().order_by('pid'))

        # Prepare headers
        all_headers = ['pid']
        model_fields_map = {}  # Keep track of field names per model

        for model in apps.get_app_config('nanopore').get_models():
            model_name = model.__name__
            if model_name == 'Screening':
                continue  # PID is already first column

            fields = []
            headers = []

            for f in model._meta.get_fields():
                if f.name in self.exclude_fields:
                    continue
                if model_name == 'RegimenChanges' and f.name == 'screening':
                    continue
                fields.append(f)
                headers.append(f.name)

            # Add remarks column with model name
            headers.append(f"{model_name}_remarks")
            model_fields_map[model_name] = fields
            all_headers.extend(headers)

        # Write header row
        writer.writerow(all_headers)

        # Build rows per Screening
        for screening in screening_list:
            row = [screening.pid]

            for model in apps.get_app_config('nanopore').get_models():
                model_name = model.__name__
                if model_name == 'Screening':
                    continue

                fields = model_fields_map[model_name]

                # Get related object for this Screening
                try:
                    obj = model.objects.get(screening=screening)
                except model.DoesNotExist:
                    obj = None

                # Fill row with model data or empty if not exist
                if obj:
                    for f in fields:
                        try:
                            if f.many_to_many:
                                value = getattr(obj, f.name).all()
                                row.append(';'.join(str(v.pk) for v in value))
                            elif f.one_to_one and f.related_model.__name__ == 'Screening':
                                # Already have PID
                                continue
                            elif f.many_to_one or f.one_to_one:
                                value = getattr(obj, f.name, None)
                                row.append(value.pk if value else '')
                            else:
                                row.append(getattr(obj, f.name))
                        except (AttributeError, f.related_model.DoesNotExist):
                            row.append('')
                    # Append remarks
                    row.append(getattr(obj, 'remarks', '') or '')
                else:
                    # Fill empty columns
                    row.extend([''] * (len(fields) + 1))  # +1 for remarks

            writer.writerow(row)

        return response
