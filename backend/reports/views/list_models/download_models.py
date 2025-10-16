from django.views import View
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.apps import apps
import csv

# Decorator to restrict access to staff
def staff_required(view_func):
    return method_decorator(staff_member_required, name='dispatch')(view_func)

# @staff_required
class ExportModelDataView(View):
    """
    Export any model data to CSV dynamically.
    ForeignKeys will export `.name` if available.
    ManyToMany fields will export semicolon-separated values.
    """

    # Fields to exclude
    exclude_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def get(self, request, model_name):
        # Get model dynamically
        try:
            model = apps.get_model('nanopore', model_name)  # change 'nanopore' to your app name
        except LookupError:
            return HttpResponse("Unknown model", status=404)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_data.csv"'

        writer = csv.writer(response)

        # Get concrete fields (normal + ForeignKey) except excluded
        fields = [f for f in model._meta.get_fields() if f.concrete and f.name not in self.exclude_fields]
        # Get ManyToMany fields
        m2m_fields = [f for f in model._meta.get_fields() if f.many_to_many and f.name not in self.exclude_fields]

        # Header row
        header = [f.name for f in fields] + [f.name for f in m2m_fields]
        writer.writerow(header)

        # Write data rows
        for obj in model.objects.all():
            row = []
            # Normal + FK fields
            for field in fields:
                value = getattr(obj, field.name)
                if hasattr(value, 'name'):
                    value = value.name
                row.append(value)
            # ManyToMany fields
            for field in m2m_fields:
                related_objs = getattr(obj, field.name).all()
                # Join names or str() with semicolon
                row.append("; ".join([str(r) for r in related_objs]))
            writer.writerow(row)

        return response
