from django.shortcuts import render
from django.apps import apps

def list_all_models_view(request):
    """Render template listing all models available for export"""
    model_names = ["Screening", "Enrollment", "Diagnosis", "ClinicLaboratory", "ZonalLaboratory"]
    models_list = []

    for name in model_names:
        model = apps.get_model("nanopore", name)
        count = model.objects.count()
        models_list.append({
            "name": name,
            "description": getattr(model, "description", ""),
            "count": count,
            "download_url": f"/reports/export-models/?model={name}&mode=full"
        })

    return render(request, "reports/data_export/export_models.html", {"models_list": models_list})
