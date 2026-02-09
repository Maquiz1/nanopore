from django.views import View
from django.http import StreamingHttpResponse
import csv
import io
from django.apps import apps

REGIMEN_FIELDS = ["date", "drug", "changes", "reason", "specify"]

class ExportModelDataView(View):
    exclude_fields = ['id','created_at','updated_at','created_by','updated_by','screening','enrollment','clinic_laboratory','zonal_laboratory','diagnosis','regimen_changes','remarks']

    def get_models(self, model_name=None):
        if model_name:
            model = apps.get_model("nanopore", model_name)
            return [model]
        return [apps.get_model("nanopore","Screening")]

    def get(self, request):
        mode = request.GET.get("mode","full")
        model_name = request.GET.get("model")
        models_list = self.get_models(model_name)

        def csv_generator():
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            # Header
            headers = []
            for model in models_list:
                for f in model._meta.fields:
                    if f.name not in self.exclude_fields:
                        headers.append(f.name)
            if models_list[0]._meta.model_name == "screening":
                for f in REGIMEN_FIELDS:
                    headers.append(f"regimen_{f}")
            writer.writerow(headers)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

            qs = models_list[0].objects.all().iterator()

            for obj in qs:
                row = []
                for f in models_list[0]._meta.fields:
                    if f.name in self.exclude_fields:
                        continue
                    val = getattr(obj,f.name,"")
                    if f.is_relation:
                        if f.many_to_many:
                            val = ";".join(str(v) for v in getattr(obj,f.name).all())
                        else:
                            related = getattr(obj,f.name,None)
                            if mode=="values_only":
                                val = related.pk if related else ""
                            elif mode=="labels_only":
                                val = str(related) if related else ""
                    row.append(val)

                if models_list[0]._meta.model_name=="screening":
                    regimens = list(obj.regimen_changes.all().order_by("date")) or [None]
                    for regimen in regimens:
                        for f in REGIMEN_FIELDS:
                            row.append(getattr(regimen,f,"") or "")
                writer.writerow(row)
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

        filename = f"{model_name or 'model_data'}.csv"
        response = StreamingHttpResponse(csv_generator(), content_type="text/csv")
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ExportAllModelsCombinedView(View):
    exclude_fields = ['id','created_at','updated_at','created_by','updated_by','screening','enrollment','clinic_laboratory','zonal_laboratory','diagnosis','regimen_changes','remarks']

    def get_models(self):
        return {
            "screening": apps.get_model("nanopore","Screening"),
            "enrollment": apps.get_model("nanopore","Enrollment"),
            "diagnosis": apps.get_model("nanopore","Diagnosis"),
            "clinic": apps.get_model("nanopore","ClinicLaboratory"),
            "zonal": apps.get_model("nanopore","ZonalLaboratory")
        }

    def get(self, request):
        mode = request.GET.get("mode","full")
        models = self.get_models()
        Screening = models["screening"]

        def csv_generator():
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            headers = []
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

            qs = Screening.objects.all().select_related('enrollment','diagnosis','clinic_laboratory','zonal_laboratory').prefetch_related('regimen_changes').iterator()

            for screening in qs:
                enrollment = getattr(screening,"enrollment",None)
                diagnosis = getattr(screening,"diagnosis",None)
                clinic = getattr(screening,"clinic_laboratory",None)
                zonal = getattr(screening,"zonal_laboratory",None)
                regimens = list(screening.regimen_changes.all().order_by("date")) or [None]

                for regimen in regimens:
                    row=[]
                    def get_value(obj,f):
                        if not obj: return ""
                        val = getattr(obj,f.name,"")
                        if f.is_relation:
                            if f.many_to_many:
                                return ";".join(str(v) for v in getattr(obj,f.name).all())
                            else:
                                related = getattr(obj,f.name,None)
                                if mode=="values_only": return related.pk if related else ""
                                elif mode=="labels_only": return str(related) if related else ""
                                else: return str(related) if related else ""
                        return val

                    for key,obj_instance in [("screening",screening),("enrollment",enrollment),("diagnosis",diagnosis),("clinic",clinic),("zonal",zonal)]:
                        model = models[key]
                        for f in model._meta.fields:
                            if f.name in self.exclude_fields: continue
                            row.append(get_value(obj_instance,f))

                    if regimen:
                        for f in REGIMEN_FIELDS:
                            row.append(getattr(regimen,f,"") or "")
                    else:
                        row.extend([""]*len(REGIMEN_FIELDS))

                    writer.writerow(row)
                    yield buffer.getvalue()
                    buffer.seek(0)
                    buffer.truncate(0)

        response = StreamingHttpResponse(csv_generator(), content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="all_models_combined.csv"'
        return response
