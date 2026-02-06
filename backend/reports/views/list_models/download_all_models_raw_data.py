from django.views import View
from django.http import StreamingHttpResponse
from django.apps import apps
import csv
import io

REGIMEN_FIELDS = ["date", "drug", "changes", "reason", "specify"]

class ExportAllModelsRawDataView(View):

    # Fields to exclude from all models
    exclude_fields = [
        'id', 'pid1', 'pid2', 'created_at', 'updated_at',
        'created_by', 'updated_by',
        'screening', 'enrollment', 'clinic_laboratory',
        'zonal_laboratory', 'diagnosis', 'regimen_changes',
        'remarks'
    ]

    def get(self, request):
        mode = request.GET.get("mode", "full")  # full, values_only, labels_only

        # Load models
        Screening = apps.get_model("nanopore", "Screening")
        Enrollment = apps.get_model("nanopore", "Enrollment")
        Diagnosis = apps.get_model("nanopore", "Diagnosis")
        ClinicLaboratory = apps.get_model("nanopore", "ClinicLaboratory")
        ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")

        models_list = [Screening, Enrollment, Diagnosis, ClinicLaboratory, ZonalLaboratory]

        def csv_generator():
            pseudo_buffer = io.StringIO()
            writer = csv.writer(pseudo_buffer)

            # Build headers
            headers = []
            for model in models_list:
                for f in model._meta.fields:
                    if f.name not in self.exclude_fields:
                        headers.append(f.name)
            for f in REGIMEN_FIELDS:
                headers.append("regimen_" + f)

            writer.writerow(headers)
            yield pseudo_buffer.getvalue()
            pseudo_buffer.seek(0)
            pseudo_buffer.truncate(0)

            # Fetch screenings with optimized queries
            screenings_qs = Screening.objects.all()\
                .select_related('enrollment','diagnosis','clinic_laboratory','zonal_laboratory')\
                .prefetch_related('regimen_changes')\
                .order_by("pid")\
                .iterator()

            for screening in screenings_qs:
                enrollment = getattr(screening,'enrollment',None)
                diagnosis = getattr(screening,'diagnosis',None)
                clinic = getattr(screening,'clinic_laboratory',None)
                zonal = getattr(screening,'zonal_laboratory',None)

                regimens = list(screening.regimen_changes.all().order_by("date")) or [None]

                for regimen in regimens:
                    row = []

                    # Helper to get human-readable value
                    def get_value(obj, f):
                        if not obj:
                            return ""
                        val = getattr(obj,f.name,"")
                        # Choice fields
                        if getattr(f,"choices", None):
                            val = dict(f.choices).get(val,val)
                        # ForeignKey / OneToOne
                        if f.is_relation:
                            if f.many_to_many:
                                return ";".join(str(v) for v in getattr(obj,f.name).all())
                            else:
                                return str(val) if val else ""
                        return val

                    # Write fields for each model
                    for model, obj in zip(models_list,[screening,enrollment,diagnosis,clinic,zonal]):
                        for f in model._meta.fields:
                            if f.name in self.exclude_fields:
                                continue
                            row.append(get_value(obj,f))

                    # Regimen fields
                    if regimen:
                        for f in REGIMEN_FIELDS:
                            row.append(str(getattr(regimen,f,"")) if getattr(regimen,f,None) else "")
                    else:
                        row.extend([""]*len(REGIMEN_FIELDS))

                    writer.writerow(row)
                    yield pseudo_buffer.getvalue()
                    pseudo_buffer.seek(0)
                    pseudo_buffer.truncate(0)

        # Streaming response
        response = StreamingHttpResponse(
            csv_generator(),
            content_type="text/csv"
        )
        filename = "all_models.csv"
        if mode == "values_only":
            filename = "all_models_values.csv"
        elif mode == "labels_only":
            filename = "all_models_labels.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
