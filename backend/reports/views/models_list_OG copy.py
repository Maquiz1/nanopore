# reports/views/models_list.py
from django.views.generic import TemplateView
from django.urls import reverse
from django.apps import apps

class ModelsListView(TemplateView):
    template_name = "reports/models_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # List of models with their app_label and export URLs
        models_info = [
            {"app_label": "nanopore", "model_name": "Screening", "export_url": reverse("reports:download-all-csv")},
            {"app_label": "nanopore", "model_name": "Enrollment", "export_url": reverse("reports:download-all-csv")},
            {"app_label": "nanopore", "model_name": "ClinicLaboratory", "export_url": reverse("reports:download-all-csv")},
            {"app_label": "nanopore", "model_name": "Diagnosis", "export_url": reverse("reports:download-all-csv")},
            {"app_label": "nanopore", "model_name": "ZonalLaboratory", "export_url": reverse("reports:download-all-csv")},
            {"app_label": "nanopore", "model_name": "RegimenChanges", "export_url": reverse("reports:download-all-csv")},
            # Add more models here if needed
        ]

        models_list = []
        for info in models_info:
            try:
                model_class = apps.get_model(info["app_label"], info["model_name"])
                count = model_class.objects.count()
            except LookupError:
                count = 0
            models_list.append({
                "name": info["model_name"],
                "count": count,
                "export_url": info["export_url"],
            })

        context["models"] = models_list
        return context
