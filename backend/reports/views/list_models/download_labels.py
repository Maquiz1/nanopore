from django.views import View
from django.http import HttpResponse
from django.apps import apps
import importlib
import csv


class DownloadModelLabelsView(View):
    """
    Export CSV with form labels as column headers (if available),
    exporting readable names for ForeignKey and ManyToMany fields.
    """

    exclude_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get(self, request, model_name):
        try:
            # Dynamically get model from app
            model = apps.get_model('nanopore', model_name)
        except LookupError:
            return HttpResponse("Unknown model", status=404)

        # Try to import form for this model
        form_class = None
        try:
            forms_module = importlib.import_module(f"{model._meta.app_label}.forms")
            form_class = getattr(forms_module, f"{model_name}Form", None)
        except ModuleNotFoundError:
            pass

        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_data.csv"'
        writer = csv.writer(response)

        # Get model fields
        fields = [
            f for f in model._meta.get_fields()
            if f.concrete and not f.auto_created and f.name not in self.exclude_fields
        ]

        # Get ManyToMany fields
        m2m_fields = [
            f for f in model._meta.get_fields()
            if f.many_to_many and f.name not in self.exclude_fields
        ]

        # Build headers (use form labels if available)
        if form_class:
            form = form_class()
            headers = []
            for f in fields + m2m_fields:
                field_obj = form.fields.get(f.name)
                if field_obj and field_obj.label:
                    headers.append(field_obj.label)
                else:
                    headers.append(f.verbose_name.title())
        else:
            headers = [f.verbose_name.title() for f in fields + m2m_fields]

        writer.writerow(headers)

        # Write data rows
        for obj in model.objects.all():
            row = []

            # Handle normal + FK fields
            for f in fields:
                value = getattr(obj, f.name)
                if f.many_to_one or f.one_to_one:
                    # Prefer readable name if available
                    if value:
                        row.append(getattr(value, 'name', str(value)))
                    else:
                        row.append('')
                else:
                    row.append(value)

            # Handle ManyToMany fields
            for f in m2m_fields:
                related_objs = getattr(obj, f.name).all()
                # Join readable names or str()
                row.append("; ".join([getattr(r, 'name', str(r)) for r in related_objs]))

            writer.writerow(row)

        return response
