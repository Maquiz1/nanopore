import os
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.forms.laboratory.edcs_tblis.tblis_raw_upload_form import TblisRawUploadForm
from nanopore.tasks_tblis_raw import process_raw_tblis_upload

class TblisRawUploadView(LoginRequiredMixin, View):
    template_name = "nanopore/laboratory/edcs_tblis/tblis_raw_upload.html"

    def get(self, request):
        return render(request, self.template_name, {"form": TblisRawUploadForm()})

    def post(self, request):
        form = TblisRawUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        file_instance = request.FILES["file"]
        file_path = os.path.join("media", "imports", "tblis_raw", file_instance.name)

        # Make sure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the uploaded file in chunks so memory doesn't crash on large files
        with open(file_path, "wb+") as destination:
            for chunk in file_instance.chunks():
                destination.write(chunk)

        # Pass absolute path to Celery for background processing
        task = process_raw_tblis_upload.delay(file_path, request.user.id)

        return JsonResponse({"task_id": task.id})
