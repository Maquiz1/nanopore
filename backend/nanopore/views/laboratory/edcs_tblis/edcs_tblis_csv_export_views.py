import json
import os
import uuid
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from nanopore.tasks_csv_export import export_edcs_tblis_csv


class TriggerCsvExportView(LoginRequiredMixin, View):
    """
    POST: enqueue the background Excel export and return task_id.
    Accepts filters as JSON body OR as GET/POST params.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Try JSON body first, fall back to GET/POST params
        try:
            body = json.loads(request.body or "{}")
        except (json.JSONDecodeError, ValueError):
            body = {}

        def _get(key):
            return body.get(key) or request.GET.get(key) or request.POST.get(key) or ""

        filters = {
            "zone": _get("zone"),
            "site": _get("site"),
            "pid": _get("pid"),
            "unique_lab_no": _get("unique_lab_no"),
            "substudy": _get("substudy"),
            "missing_culture_substudy": _get("missing_culture_substudy"),
            "missing_culture": _get("missing_culture"),
            "card_type": _get("card_type"),
        }

        card_type = filters.get("card_type") or "data"
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"export_{card_type}_{date_str}_{uuid.uuid4().hex[:8]}.xlsx"
        task = export_edcs_tblis_csv.delay(filters=filters, filename=filename, user_id=request.user.id)
        return JsonResponse({"task_id": task.id, "filename": filename})


class ServeCsvExportView(LoginRequiredMixin, View):
    """
    GET: serve the generated Excel file for download once ready.
    """
    def get(self, request, filename, *args, **kwargs):
        filepath = os.path.join(settings.MEDIA_ROOT, "exports", filename)
        if not os.path.exists(filepath):
            raise Http404("Export file not found.")
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if filename.endswith(".xlsx")
            else "text/csv"
        )
        response = FileResponse(
            open(filepath, "rb"),
            content_type=content_type,
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
