import os
from django.conf import settings
from django.views import View
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.apps import apps
from reports.tasks_export_models import export_model_raw_data_task

def staff_required(view_func):
    return method_decorator(staff_member_required, name='dispatch')(view_func)

# @staff_required
class TriggerModelExportView(View):
    """
    POST: enqueue the background CSV export for the given model and return task_id.
    """
    def get(self, request, model_name, *args, **kwargs):
        # We handle GET here so the existing link triggers it dynamically via JS
        task = export_model_raw_data_task.delay(model_name)
        return JsonResponse({"task_id": task.id})

# @staff_required
class ServeModelExportView(View):
    """
    GET: serve the generated CSV file for download once ready.
    """
    def get(self, request, filename, *args, **kwargs):
        filepath = os.path.join(settings.MEDIA_ROOT, "exports", filename)
        if not os.path.exists(filepath):
            raise Http404("Export file not found.")
        response = FileResponse(
            open(filepath, "rb"),
            content_type="text/csv",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
