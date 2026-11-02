from utils import access
from utils.access import export_queryset
from utils.access_mixins import FeatureAccessMixin
import logging

from django.views import View
from django.http import StreamingHttpResponse, HttpResponse
import csv
import io
from django.apps import apps

logger = logging.getLogger(__name__)

REGIMEN_FIELDS = ["date", "drug", "changes", "reason", "specify"]

# Fields guaranteed to appear first in every export, regardless of _meta.fields
# ordering or editable=False.  Values are read via getattr() then obj.__dict__
# as a fallback (bypasses ORM descriptors that can suppress editable=False values).
PRIORITY_FIELDS = ["pid", "pid1", "pid2"]


def is_coded(field):
    """An answer from an option list: its code is the `value` the codebook lists (the row id can differ)."""
    return any(f.name == "value" for f in field.related_model._meta.fields)


def field_headers(field, mode, name=None):
    name = name or field.name
    if mode == "full" and field.is_relation and is_coded(field):
        return [name, f"{name}_label"]
    return [name]


def relation_cells(field, related, mode):
    """Full: code and label. Codes: the code. Labels: the label. Links that have no code (site) show their name."""
    label = str(related) if related else ""
    if not is_coded(field):
        return [label]
    code = ""
    if related:
        code = related.value if related.value is not None else related.pk
    if mode == "full":
        return [code, label]
    return [code] if mode == "values_only" else [label]


class ExportModelDataView(FeatureAccessMixin, View):
    access_feature = access.EXPORTS
    exclude_fields = [
        'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'screening', 'enrollment', 'clinic_laboratory', 'zonal_laboratory',
        'diagnosis', 'regimen_changes', 'remarks',
    ]

    def get_models(self, model_name=None):
        if model_name:
            model = apps.get_model("nanopore", model_name)
            return [model]
        return [apps.get_model("nanopore", "Screening")]

    def _model_has_field(self, model, field_name):
        return any(f.name == field_name for f in model._meta.fields)

    def _build_select_related(self, model):
        """Return a list of FK field names for select_related to avoid N+1 queries."""
        return [
            f.name for f in model._meta.fields
            if f.is_relation and not f.many_to_many and f.name not in self.exclude_fields
        ]

    def get(self, request):
        mode = request.GET.get("mode", "full")
        model_name = request.GET.get("model")
        models_list = self.get_models(model_name)
        model = models_list[0]

        # Determine which priority fields actually exist on this model
        active_priority = [f for f in PRIORITY_FIELDS if self._model_has_field(model, f)]
        # Forms linked to a participant without their own pid column get the
        # participant's PID from the screening, so every row can be matched.
        pid_from_screening = "pid" not in active_priority and self._model_has_field(model, "screening")

        # Pre-build select_related list (avoids N+1 FK lookups on every row)
        related_fields = self._build_select_related(model)

        def csv_generator():
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            try:
                # ── Header ─────────────────────────────────────────────────
                headers = (["pid"] if pid_from_screening else []) + list(active_priority)
                for f in model._meta.fields:
                    if f.name not in self.exclude_fields and f.name not in active_priority:
                        headers.extend(field_headers(f, mode))
                if model._meta.model_name == "screening":
                    regimen_fields = [apps.get_model("nanopore", "RegimenChanges")._meta.get_field(f) for f in REGIMEN_FIELDS]
                    for f in regimen_fields:
                        headers.extend(field_headers(f, mode, f"regimen_{f.name}"))
                writer.writerow(headers)
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

                # ── Rows ────────────────────────────────────────────────────
                # select_related prevents N+1: ZonalLab has 30+ FK fields —
                # without this, each row fires 30+ extra DB queries → timeout.
                site_field = "site" if model._meta.model_name == "screening" else "screening__site"
                records = export_queryset(request.user, model.objects.all(), site_field)
                pids = {}
                if pid_from_screening:
                    # One extra query instead of one more join (lab models already join ~60 tables).
                    Screening = apps.get_model("nanopore", "Screening")
                    pids = dict(Screening.objects.filter(pk__in=records.values("screening_id")).values_list("pk", "pid"))
                qs = records.select_related(*related_fields).iterator(chunk_size=200)

                for obj in qs:
                    row = [pids.get(obj.screening_id, "")] if pid_from_screening else []

                    # 1. Priority fields — __dict__ fallback bypasses ORM
                    #    descriptors that can suppress editable=False values.
                    for field_name in active_priority:
                        val = obj.__dict__.get(field_name) or getattr(obj, field_name, "") or ""
                        row.append(val)

                    # 2. Remaining model fields
                    for f in model._meta.fields:
                        if f.name in self.exclude_fields or f.name in active_priority:
                            continue

                        if f.is_relation and not f.many_to_many:
                            row.extend(relation_cells(f, getattr(obj, f.name, None), mode))  # already selected
                        else:
                            row.append(getattr(obj, f.name, "") or "")

                    # 3. Regimen columns (screening only)
                    if model._meta.model_name == "screening":
                        regimens = list(obj.regimen_changes.all().order_by("date")) or [None]
                        for regimen in regimens:
                            for f in regimen_fields:
                                if f.is_relation:
                                    row.extend(relation_cells(f, getattr(regimen, f.name, None), mode))
                                else:
                                    row.append(getattr(regimen, f.name, "") or "")

                    writer.writerow(row)
                    yield buffer.getvalue()
                    buffer.seek(0)
                    buffer.truncate(0)

            except Exception as exc:
                logger.exception(
                    "Export failed for model=%s mode=%s: %s",
                    model_name, mode, exc
                )
                # Yield a clearly marked error row so the CSV is not silently truncated
                writer.writerow([f"EXPORT ERROR: {exc}"])
                yield buffer.getvalue()

        filename = f"{model_name or 'model_data'}.csv"
        response = StreamingHttpResponse(csv_generator(), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response




from django.http import JsonResponse
from reports.tasks_export_models import export_all_models_combined_task

class ExportAllModelsCombinedView(FeatureAccessMixin, View):
    """Queues the combined export (all forms in one row per participant) and returns the task id."""
    access_feature = access.EXPORTS

    def get(self, request):
        mode = "edcs" if request.GET.get("with") == "edcs" else "zonal"
        task = export_all_models_combined_task.delay(mode=mode, user_id=request.user.id)
        return JsonResponse({"task_id": task.id})
