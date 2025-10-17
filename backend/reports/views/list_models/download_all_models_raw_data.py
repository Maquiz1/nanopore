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
    Export all models' data into a single CSV aligned by Screening.pid.
    PID is the first column. Screening includes all its columns.
    Other models are mapped via their Screening relation.
    Columns are ordered:
    Screening → Enrollment → ClinicLaboratory → Diagnosis → ZonalLaboratory → RegimenChanges
    Remarks columns are prefixed with the model name.
    """

    exclude_fields = [
        'id', 'pid1', 'pid2', 'created_at', 'updated_at', 'created_by', 'updated_by'
    ]

    model_order = [
        'Screening',
        'Enrollment',
        'ClinicLaboratory',
        'Diagnosis',
        'ZonalLaboratory',
        'RegimenChanges',
    ]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_models_by_screening.csv"'
        writer = csv.writer(response)

        # Get Screening objects
        Screening = apps.get_model('nanopore', 'Screening')
        screening_list = list(Screening.objects.all().order_by('pid'))

        all_headers = []
        model_fields_map = {}

        # Prepare headers and fields
        for model_name in self.model_order:
            model = apps.get_model('nanopore', model_name)
            fields = []
            headers = []

            for f in model._meta.get_fields():
                if f.name in self.exclude_fields:
                    continue
                # Skip Screening FK in other models
                if model_name != 'Screening' and f.one_to_one and f.related_model.__name__ == 'Screening':
                    continue
                fields.append(f)
                headers.append(f.name)

            # Add model-specific remarks for non-Screening models
            if model_name != 'Screening':
                headers.append(f"{model_name}_remarks")

            model_fields_map[model_name] = fields
            all_headers.extend(headers)

        # Write headers
        writer.writerow(all_headers)

        # Build rows per Screening
        for screening in screening_list:
            row = []

            for model_name in self.model_order:
                model = apps.get_model('nanopore', model_name)
                fields = model_fields_map[model_name]

                if model_name == 'Screening':
                    obj = screening
                else:
                    try:
                        obj = model.objects.get(screening=screening)
                    except model.DoesNotExist:
                        obj = None

                if obj:
                    for f in fields:
                        try:
                            if f.many_to_many:
                                value = getattr(obj, f.name).all()
                                row.append(';'.join(str(v.pk) for v in value))
                            elif f.one_to_one and f.related_model.__name__ == 'Screening':
                                # skip PID, already in Screening
                                continue
                            elif f.many_to_one or f.one_to_one:
                                value = getattr(obj, f.name, None)
                                row.append(value.pk if value else '')
                            else:
                                row.append(getattr(obj, f.name))
                        except (AttributeError, f.related_model.DoesNotExist):
                            row.append('')
                    # Append model-specific remarks
                    row.append(getattr(obj, 'remarks', '') or '')
                else:
                    # Fill empty columns (fields + remarks)
                    fill_len = len(fields) + (1 if model_name != 'Screening' else 0)
                    row.extend([''] * fill_len)

            writer.writerow(row)

        return response
