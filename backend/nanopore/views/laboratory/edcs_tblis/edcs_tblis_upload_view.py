import os
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from nanopore.forms.laboratory.edcs_tblis.edcs_tblis_lab_upload_form import EdcsTBLISLabUploadForm
from nanopore.tasks import import_edcs_tblis


class EdcsTBLISCsvUploadView(View):
    template_name = "nanopore/laboratory/edcs_tblis/edcs_tblis_laboratory_upload.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": EdcsTBLISLabUploadForm()}
        )

    def post(self, request):
        form = EdcsTBLISLabUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form}
            )

        file_instance = request.FILES["file"]
        file_path = os.path.join("media", "imports", file_instance.name)

        # Make sure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the uploaded file
        with open(file_path, "wb+") as destination:
            for chunk in file_instance.chunks():
                destination.write(chunk)

        # Pass absolute path to Celery
        task = import_edcs_tblis.delay(file_path)

        return JsonResponse({"task_id": task.id})