import os
from django.conf import settings
from django.views import View
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.apps import apps
from reports.tasks_export_models import export_model_raw_data_task
from utils import access
from utils.access import is_unscoped
from utils.access_mixins import FeatureAccessMixin

def staff_required(view_func):
    return method_decorator(staff_member_required, name='dispatch')(view_func)

# @staff_required
class TriggerModelExportView(FeatureAccessMixin, View):
    access_feature = access.EXPORTS

    """
    POST: enqueue the background CSV export for the given model and return task_id.
    """
    def get(self, request, model_name, *args, **kwargs):
        # We handle GET here so the existing link triggers it dynamically via JS
        task = export_model_raw_data_task.delay(model_name, user_id=request.user.id)
        return JsonResponse({"task_id": task.id})

# @staff_required
class ServeModelExportView(FeatureAccessMixin, View):
    access_feature = access.EXPORTS

    """
    GET: serve the generated CSV file for download once ready.
    """
    def get(self, request, filename, *args, **kwargs):
        # Scoped users may only fetch the files generated for them.
        if not is_unscoped(request.user) and not filename.endswith(f"_u{request.user.id}.csv"):
            raise Http404("Export file not found.")
        filename = os.path.basename(filename)
        filepath = os.path.join(settings.MEDIA_ROOT, "exports", filename)
        if not os.path.exists(filepath):
            raise Http404("Export file not found.")
        response = FileResponse(
            open(filepath, "rb"),
            content_type="text/csv",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
