# nanopore/views/diagnosis/diagnosis_form_views.py
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from nanopore.models import Diagnosis, Screening
from nanopore.forms.diagnosis.diagnosisform import DiagnosisForm


class DiagnosisFormView(LoginRequiredMixin, View):
    template_name = "nanopore/diagnosis/diagnosis_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")

    def get_object(self):
        """Return the Diagnosis object if updating, else None."""
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(Diagnosis, pk=pk)
        return None

    def get_screening_instance(self):
        """Return Screening instance for creation or update."""
        obj = self.get_object()
        if obj:
            return obj.screening
        screening_id = self.request.GET.get("screening")
        if screening_id:
            return get_object_or_404(Screening, pk=screening_id)
        return None

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()

        # Initialize form with screening_instance
        form = DiagnosisForm(
            instance=obj,
            initial={"screening": screening_instance},
            screening_instance=screening_instance
        )

        return render(
            request,
            self.template_name,
            {"form": form, "object": obj, "screening": screening_instance}
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()

        # Bind form with POST data
        form = DiagnosisForm(
            request.POST,
            instance=obj,
            screening_instance=screening_instance
        )

        if form.is_valid():
            diagnosis = form.save(commit=False)
            diagnosis.updated_by = request.user
            diagnosis.updated_at = timezone.now()

            if not diagnosis.pk:
                diagnosis.created_by = request.user
                # screening is assigned inside form.save()

            try:
                diagnosis.save()
                form.save_m2m()
            except Exception as e:
                form.add_error(None, str(e))
                return render(request, self.template_name, {"form": form, "object": obj, "screening": screening_instance})

            return redirect(self.success_url)


        return render(
            request,
            self.template_name,
            {"form": form, "object": obj, "screening": screening_instance}
        )
