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
class DownloadModelLabelsView(View):
    """
    Export labels CSV: ForeignKey names and choice field names
    """
    exclude_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get(self, request, model_name):
        try:
            model = apps.get_model('nanopore', model_name)
        except LookupError:
            return HttpResponse("Unknown model", status=404)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_labels.csv"'
        writer = csv.writer(response)

        fields = [f for f in model._meta.get_fields() if f.concrete and not f.auto_created and f.name not in self.exclude_fields]

        for f in fields:
            # ForeignKey → export __str__() values of related objects
            if f.many_to_one or f.one_to_one:
                related_model = f.related_model
                labels = [str(obj) for obj in related_model.objects.all()]
                writer.writerow([f.name] + labels)

            # Choice fields → export readable choices
            elif hasattr(f, 'choices') and f.choices:
                choices = [c[1] for c in f.choices]
                writer.writerow([f.name] + choices)

        return response