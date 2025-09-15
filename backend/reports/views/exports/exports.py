# reports/views/exports.py
import csv
from datetime import date
from django.apps import apps
from django.http import HttpResponse
from django.views import View

class ModelCsvExportView(View):
    """Export any model dynamically to CSV with optional column exclusion and FK choice"""

    # Optional: columns to exclude per model
    EXCLUDE_FIELDS = {
        "Screening": ["id","screening","created_at","updated_at","created_by","updated_by"],
        "Enrollment": ["id","screening","created_at","updated_at","created_by","updated_by"],
        "ClinicLaboratory": ["id","screening","created_at","updated_at","created_by","updated_by"],
        "Diagnosis": ["id","screening","created_at","updated_at","created_by","updated_by"],
        "ZonalLaboratory": ["id","screening","created_at","updated_at","created_by","updated_by"],
        "RegimenChanges": ["id","screening","created_at","updated_at","created_by","updated_by"],
    }

    def get(self, request, app_label, model_name, *args, **kwargs):
        try:
            model_class = apps.get_model(app_label, model_name)
        except LookupError:
            return HttpResponse(f"Model {app_label}.{model_name} not found", status=404)

        qs = model_class.objects.all()
        if not qs.exists():
            return HttpResponse("No records found", status=204)

        # Get FK choice: names or values
        fk_type = request.GET.get("fk", "names")  # 'names' or 'values'
        # Optional: custom filename
        custom_name = request.GET.get("filename", model_name)
        today_str = date.today().strftime("%Y-%m-%d")
        filename = f"{custom_name}_{today_str}.csv"

        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)

        # Determine fields, exclude as needed
        exclude_fields = self.EXCLUDE_FIELDS.get(model_name, [])
        fields = [
            f.name for f in model_class._meta.get_fields()
            if not f.many_to_many and not f.one_to_many and f.name not in exclude_fields
        ]

        # Write header
        writer.writerow(fields)

        # Write data rows
        for obj in qs:
            row = []
            for f in fields:
                val = getattr(obj, f)
                # Handle ForeignKey safely
                if hasattr(val, "name"):
                    val = val.name if fk_type == "names" else getattr(val, 'id', '')
                row.append(val)
            writer.writerow(row)

        return response
