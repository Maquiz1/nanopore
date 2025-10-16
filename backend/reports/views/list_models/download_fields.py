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
class DownloadModelFieldsView(View):
    """
    Export dataset CSV: real field values, ForeignKeys as IDs
    """
    exclude_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get(self, request, model_name):
        try:
            model = apps.get_model('nanopore', model_name)
        except LookupError:
            return HttpResponse("Unknown model", status=404)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_data.csv"'
        writer = csv.writer(response)

        fields = [f for f in model._meta.get_fields() if f.concrete and not f.auto_created and f.name not in self.exclude_fields]
        writer.writerow([f.name for f in fields])

        for obj in model.objects.all():
            row = []
            for f in fields:
                val = getattr(obj, f.name)
                # For ForeignKeys → store pk / ID
                if f.many_to_one or f.one_to_one:
                    row.append(val.pk if val else '')
                else:
                    row.append(val)
            writer.writerow(row)

        return response