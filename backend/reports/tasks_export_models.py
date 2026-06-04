import csv
import os
from celery import shared_task
from django.conf import settings
from django.apps import apps


@shared_task(bind=True)
def export_model_raw_data_task(self, model_name, filename=None):
    if not filename:
        filename = f"{model_name}_raw_data_export.csv"

    try:
        model = apps.get_model('nanopore', model_name)
    except LookupError:
        return {"state": "FAILURE", "error": f"Unknown model {model_name}"}

    export_dir = os.path.join(settings.MEDIA_ROOT, "exports")
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, filename)

    exclude_fields = [
        'id', 'pid1', 'pid2', 'created_at', 'updated_at', 'created_by', 'updated_by', 'remarks',
        'enrollment', 'clinic_laboratory', 'zonal_laboratory', 'diagnosis', 'regimen_changes'
    ]

    # Determine fields
    fields = []
    header = []
    select_related_fields = []
    prefetch_related_fields = []

    for f in model._meta.get_fields():
        if f.name in exclude_fields:
            continue
        if model_name == 'RegimenChanges' and f.name == 'screening':
            continue

        fields.append(f)

        if f.one_to_one and f.related_model and f.related_model.__name__ == 'Screening':
            header.append('pid')
        else:
            header.append(f.name)

        if f.many_to_one or f.one_to_one:
            select_related_fields.append(f.name)
        elif f.many_to_many:
            prefetch_related_fields.append(f.name)

    remarks_field_name = f"{model_name.lower()}_remarks"
    header.append(remarks_field_name)

    total = model.objects.count()
    if total == 0:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
        return {"state": "SUCCESS", "file": filename, "total": 0}

    qs = model.objects.all()
    if select_related_fields:
        qs = qs.select_related(*select_related_fields)
    if prefetch_related_fields:
        qs = qs.prefetch_related(*prefetch_related_fields)

    # Use iterator for memory efficiency
    qs = qs.iterator(chunk_size=500)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for i, obj in enumerate(qs, start=1):
            row = []
            for f in fields:
                try:
                    if f.many_to_many:
                        value = getattr(obj, f.name).all()
                        row.append(';'.join(str(v.pk) for v in value))
                    elif f.one_to_one and f.related_model and f.related_model.__name__ == 'Screening':
                        value = getattr(obj, f.name, None)
                        row.append(value.pid if value else '')
                    elif f.many_to_one or f.one_to_one:
                        value = getattr(obj, f.name, None)
                        row.append(value.pk if value else '')
                    else:
                        value = getattr(obj, f.name)
                        row.append(value)
                except Exception:
                    row.append('')

            remarks_value = getattr(obj, 'remarks', '')
            row.append(remarks_value if remarks_value else '')

            writer.writerow(row)

            if i % 100 == 0 or i == total:
                self.update_state(
                    state="PROGRESS",
                    meta={"current": i, "total": total}
                )

    return {"state": "SUCCESS", "file": filename, "total": total}

REGIMEN_FIELDS = ["date", "drug", "changes", "reason", "specify"]

@shared_task(bind=True)
def export_all_models_combined_task(self, mode="zonal", filename=None):
    if not filename:
        filename = f"all_models_combined_{mode}.csv"

    export_dir = os.path.join(settings.MEDIA_ROOT, "exports")
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, filename)

    exclude_fields = [
        'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
        'screening', 'enrollment', 'clinic_laboratory', 'zonal_laboratory',
        'diagnosis', 'regimen_changes', 'remarks',
        'pid', 'pid1', 'pid2',  # exported once as the first columns
    ]

    models = {
        "screening":  apps.get_model("nanopore", "Screening"),
        "enrollment": apps.get_model("nanopore", "Enrollment"),
        "diagnosis":  apps.get_model("nanopore", "Diagnosis"),
        "clinic":     apps.get_model("nanopore", "ClinicLaboratory"),
    }
    
    if mode == "edcs":
        models["lab"] = apps.get_model("nanopore", "EdcsTblisZonal")
    else:
        models["lab"] = apps.get_model("nanopore", "ZonalLaboratory")
        
    Screening = models["screening"]

    def get_value(obj, f):
        if not obj:
            return ""
        val = getattr(obj, f.name, "")
        if f.is_relation:
            if f.many_to_many:
                return ";".join(str(v.pk) for v in getattr(obj, f.name).all())
            else:
                related = getattr(obj, f.name, None)
                return str(related) if related else ""
        return val

    # Headers
    headers = ["pid", "pid1", "pid2"]
    for key, model in models.items():
        for f in model._meta.fields:
            if f.name not in exclude_fields:
                headers.append(f"{key}_{f.name}")
    for f in REGIMEN_FIELDS:
        headers.append(f"regimen_{f}")

    total = Screening.objects.count()
    if total == 0:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        return {"state": "SUCCESS", "file": filename, "total": 0}

    # Pre-select based on mode
    qs = Screening.objects.all().select_related(
        'enrollment', 'diagnosis', 'clinic_laboratory'
    ).prefetch_related('regimen_changes')
    
    if mode == "edcs":
        qs = qs.select_related('tblis_laboratory')
    else:
        qs = qs.select_related('zonal_laboratory')

    qs = qs.iterator(chunk_size=500)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for i, screening in enumerate(qs, start=1):
            enrollment = getattr(screening, "enrollment", None)
            diagnosis  = getattr(screening, "diagnosis", None)
            clinic     = getattr(screening, "clinic_laboratory", None)
            
            if mode == "edcs":
                lab = getattr(screening, "tblis_laboratory", None)
            else:
                lab = getattr(screening, "zonal_laboratory", None)
                
            regimens   = list(screening.regimen_changes.all().order_by("date")) or [None]

            for regimen in regimens:
                row = []

                # 1. pid columns
                for field_name in ["pid", "pid1", "pid2"]:
                    val = getattr(screening, field_name, None)
                    if val is None or val == "":
                        val = screening.__dict__.get(field_name, "")
                    row.append(val or "")

                # 2. Each model's fields
                for key, obj_instance in [
                    ("screening",  screening),
                    ("enrollment", enrollment),
                    ("diagnosis",  diagnosis),
                    ("clinic",     clinic),
                    ("lab",        lab),
                ]:
                    model = models[key]
                    for mf in model._meta.fields:
                        if mf.name in exclude_fields:
                            continue
                        row.append(get_value(obj_instance, mf))

                # 3. Regimen columns
                if regimen:
                    for rf in REGIMEN_FIELDS:
                        row.append(getattr(regimen, rf, "") or "")
                else:
                    row.extend([""] * len(REGIMEN_FIELDS))

                writer.writerow(row)
            
            if i % 100 == 0 or i == total:
                self.update_state(state="PROGRESS", meta={"current": i, "total": total})

    return {"state": "SUCCESS", "file": filename, "total": total}
