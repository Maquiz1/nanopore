# reports/views/models_list.py
from django.views.generic import TemplateView
from django.urls import reverse
from django.apps import apps

class ModelsListView(TemplateView):
    template_name = "reports/models_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Define models you want to show
        models_info = [
            {"app_label": "nanopore", "model_name": "Screening"},
            {"app_label": "nanopore", "model_name": "Enrollment"},
            {"app_label": "nanopore", "model_name": "ClinicLaboratory"},
            {"app_label": "nanopore", "model_name": "Diagnosis"},
            {"app_label": "nanopore", "model_name": "ZonalLaboratory"},
            {"app_label": "nanopore", "model_name": "RegimenChanges"},
        ]

        models_list = []
        for info in models_info:
            try:
                model_class = apps.get_model(info["app_label"], info["model_name"])
                count = model_class.objects.count()
            except LookupError:
                count = 0

            # Dynamic export URL per model
            export_url = reverse("reports:download-model-csv", kwargs={
                "app_label": info["app_label"],
                "model_name": info["model_name"]
            })

            models_list.append({
                "name": info["model_name"],
                "count": count,
                "export_url": export_url,
            })

        context["models"] = models_list
        return context
