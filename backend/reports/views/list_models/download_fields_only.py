from django.views import View
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.apps import apps
import csv


# @method_decorator(staff_member_required, name='dispatch')
class DownloadModelFieldsView(View):
    """
    Export CSV with only real model fields (no relations, no auto fields),
    excluding timestamps and system fields.
    """

    exclude_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get(self, request, model_name):
        try:
            model = apps.get_model('nanopore', model_name)
        except LookupError:
            return HttpResponse("Unknown model", status=404)

        # Prepare HTTP response for CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_data.csv"'
        writer = csv.writer(response)

        # Include only real database fields
        fields = [
            f for f in model._meta.get_fields()
            if f.concrete and not f.auto_created and f.name not in self.exclude_fields
        ]

        # Write header
        writer.writerow([f.verbose_name.title() for f in fields])

        # Write each record
        for obj in model.objects.all():
            row = []
            for f in fields:
                val = getattr(obj, f.name)
                if f.is_relation:  # For ForeignKey or OneToOneField
                    if val is not None:
                        # Prefer readable string if available
                        row.append(str(val))
                    else:
                        row.append('')
                else:
                    row.append(val)
            writer.writerow(row)

        return response
