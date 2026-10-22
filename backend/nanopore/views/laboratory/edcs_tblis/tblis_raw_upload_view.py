from utils import access
from utils.access_mixins import FeatureAccessMixin, FormAccessMixin
import os
from uuid import uuid4
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.forms.laboratory.edcs_tblis.tblis_raw_upload_form import TblisRawUploadForm
from nanopore.tasks_tblis_raw import process_raw_tblis_upload

class TblisRawUploadView(FeatureAccessMixin, View):
    access_feature = access.TBLIS_UPLOAD
    template_name = "nanopore/laboratory/edcs_tblis/tblis_raw_upload.html"

    def get(self, request):
        return render(request, self.template_name, {"form": TblisRawUploadForm()})

    def post(self, request):
        form = TblisRawUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        file_instance = request.FILES["file"]
        original_filename = os.path.basename(file_instance.name)
        file_extension = os.path.splitext(original_filename)[1]
        stored_filename = f"{uuid4().hex}{file_extension}"
        file_path = os.path.join("media", "imports", "tblis_raw", stored_filename)

        # Make sure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the uploaded file in chunks so memory doesn't crash on large files
        with open(file_path, "wb+") as destination:
            for chunk in file_instance.chunks():
                destination.write(chunk)

        # Pass absolute path to Celery for background processing.
        # Preview runs the whole upload, then rolls every change back.
        preview = request.POST.get("preview") == "1"
        task = process_raw_tblis_upload.delay(file_path, request.user.id, original_filename, dry_run=preview)

        return JsonResponse({"task_id": task.id})


class TblisMappingDownloadView(FormAccessMixin, View):
    """TBLIS mapping document (Excel or PDF), built from the merge rules at download time."""
    access_form = access.EDCS_TBLIS

    def get(self, request, fmt):
        from django.http import Http404, HttpResponse
        from nanopore.tblis_mapping import build_mapping, to_excel, to_pdf
        if fmt not in ("excel", "pdf"):
            raise Http404("Unknown format")
        mapping = build_mapping()
        if fmt == "excel":
            content = to_excel(mapping)
            content_type, extension = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"
        else:
            content = to_pdf(mapping)
            content_type, extension = "application/pdf", "pdf"
        response = HttpResponse(content, content_type=content_type)
        stamp = mapping["version"]["generated"][:10]
        response["Content-Disposition"] = f'attachment; filename="tblis_mapping_{stamp}.{extension}"'
        return response
