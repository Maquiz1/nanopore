import os
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from nanopore.tasks_csv_export import export_edcs_tblis_csv


class TriggerCsvExportView(LoginRequiredMixin, View):
    """
    POST: enqueue the background CSV export and return task_id.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        task = export_edcs_tblis_csv.delay()
        return JsonResponse({"task_id": task.id})


class ServeCsvExportView(LoginRequiredMixin, View):
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
