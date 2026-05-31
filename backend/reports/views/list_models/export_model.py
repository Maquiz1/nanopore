from django.views import View
from django.http import StreamingHttpResponse
import csv
import io
from django.apps import apps

REGIMEN_FIELDS = ["date", "drug", "changes", "reason", "specify"]

# Fields guaranteed to appear first in every export, regardless of _meta.fields
# ordering or editable=False.  Values are read via getattr() then obj.__dict__
# as a fallback (bypasses ORM descriptors that can suppress editable=False values).
PRIORITY_FIELDS = ["pid", "pid1", "pid2"]


class ExportModelDataView(View):
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

    def get(self, request):
        mode = request.GET.get("mode", "full")
        model_name = request.GET.get("model")
        models_list = self.get_models(model_name)
        model = models_list[0]

        # Determine which priority fields actually exist on this model
        active_priority = [f for f in PRIORITY_FIELDS if self._model_has_field(model, f)]

        def csv_generator():
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            # ── Header ─────────────────────────────────────────────────────
            # Priority fields come first, then the rest (skipping duplicates)
            headers = list(active_priority)
            for f in model._meta.fields:
                if f.name not in self.exclude_fields and f.name not in active_priority:
                    headers.append(f.name)
            if model._meta.model_name == "screening":
                for f in REGIMEN_FIELDS:
                    headers.append(f"regimen_{f}")
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            # ── Rows ────────────────────────────────────────────────────────
            qs = model.objects.all().iterator()

            for obj in qs:
                row = []

                # 1. Priority fields first — use __dict__ fallback to bypass
                #    ORM descriptors that can suppress editable=False values.
                for field_name in active_priority:
                    val = getattr(obj, field_name, None)
                    if val is None or val == "":
                        val = obj.__dict__.get(field_name, "")
                    row.append(val or "")

                # 2. Remaining model fields
                for f in model._meta.fields:
                    if f.name in self.exclude_fields or f.name in active_priority:
                        continue
                    val = getattr(obj, f.name, "")
                    if f.is_relation:
                        if f.many_to_many:
                            val = ";".join(str(v) for v in getattr(obj, f.name).all())
                        else:
                            related = getattr(obj, f.name, None)
                            if mode == "values_only":
                                val = related.pk if related else ""
                            elif mode == "labels_only":
                                val = str(related) if related else ""
                    row.append(val)

                # 3. Regimen columns (screening only)
                if model._meta.model_name == "screening":
                    regimens = list(obj.regimen_changes.all().order_by("date")) or [None]
                    for regimen in regimens:
                        for f in REGIMEN_FIELDS:
                            row.append(getattr(regimen, f, "") or "")

                writer.writerow(row)
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        filename = f"{model_name or 'model_data'}.csv"
        response = StreamingHttpResponse(csv_generator(), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ExportAllModelsCombinedView(View):
    # `pid`, `pid1`, `pid2` are excluded from individual model columns because
    # they appear together at the very start of every row as universal identifiers.
    exclude_fields = [
        'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'screening', 'enrollment', 'clinic_laboratory', 'zonal_laboratory',
        'diagnosis', 'regimen_changes', 'remarks',
        'pid', 'pid1', 'pid2',  # exported once as the first columns
    ]

    def get_models(self):
        return {
            "screening":  apps.get_model("nanopore", "Screening"),
            "enrollment": apps.get_model("nanopore", "Enrollment"),
            "diagnosis":  apps.get_model("nanopore", "Diagnosis"),
            "clinic":     apps.get_model("nanopore", "ClinicLaboratory"),
            "zonal":      apps.get_model("nanopore", "ZonalLaboratory"),
        }

    def get(self, request):
        mode = request.GET.get("mode", "full")
        models = self.get_models()
        Screening = models["screening"]

        def get_value(obj, f):
            """Read a single field value from obj, applying mode formatting."""
            if not obj:
                return ""
            val = getattr(obj, f.name, "")
            if f.is_relation:
                if f.many_to_many:
                    return ";".join(str(v) for v in getattr(obj, f.name).all())
                else:
                    related = getattr(obj, f.name, None)
                    if mode == "values_only":
                        return related.pk if related else ""
                    else:
                        return str(related) if related else ""
            return val

        def csv_generator():
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            # ── Header ──────────────────────────────────────────────────────
            # First three columns are always pid, pid1, pid2 (universal row identifiers).
            # Then each model's own fields prefixed by model key (pid/pid1/pid2 excluded).
            headers = ["pid", "pid1", "pid2"]
            for key, model in models.items():
                for f in model._meta.fields:
                    if f.name not in self.exclude_fields:
                        headers.append(f"{key}_{f.name}")
            for f in REGIMEN_FIELDS:
                headers.append(f"regimen_{f}")
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            # ── Rows ─────────────────────────────────────────────────────────
            qs = (
                Screening.objects
                .all()
                .select_related(
                    'enrollment', 'diagnosis',
                    'clinic_laboratory', 'zonal_laboratory',
                )
                .prefetch_related('regimen_changes')
                .iterator()
            )

            for screening in qs:
                enrollment = getattr(screening, "enrollment", None)
                diagnosis  = getattr(screening, "diagnosis", None)
                clinic     = getattr(screening, "clinic_laboratory", None)
                zonal      = getattr(screening, "zonal_laboratory", None)
                regimens   = list(screening.regimen_changes.all().order_by("date")) or [None]

                for regimen in regimens:
                    row = []

                    # 1. pid columns — always first, use __dict__ fallback for
                    #    editable=False fields that ORM descriptors may suppress.
                    for field_name in ["pid", "pid1", "pid2"]:
                        val = getattr(screening, field_name, None)
                        if val is None or val == "":
                            val = screening.__dict__.get(field_name, "")
                        row.append(val or "")

                    # 2. Each model's fields (pid already excluded from these)
                    for key, obj_instance in [
                        ("screening",  screening),
                        ("enrollment", enrollment),
                        ("diagnosis",  diagnosis),
                        ("clinic",     clinic),
                        ("zonal",      zonal),
                    ]:
                        model = models[key]
                        for f in model._meta.fields:
                            if f.name in self.exclude_fields:
                                continue
                            row.append(get_value(obj_instance, f))

                    # 3. Regimen columns (FK to screening, one row per regimen)
                    if regimen:
                        for f in REGIMEN_FIELDS:
                            row.append(getattr(regimen, f, "") or "")
                    else:
                        row.extend([""] * len(REGIMEN_FIELDS))

                    writer.writerow(row)
                    yield buffer.getvalue()
                    buffer.seek(0)
                    buffer.truncate(0)

        response = StreamingHttpResponse(csv_generator(), content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="all_models_combined.csv"'
        return response
