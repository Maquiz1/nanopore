# nanopore/views/diagnosis/diagnosis_form_views.py
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from nanopore.models import Diagnosis, Screening, RegimenChanges
from nanopore.forms.diagnosis.diagnosisform import DiagnosisForm
from nanopore.forms.regimen.regimenform import RegimenChangesForm

class DiagnosisFormView(LoginRequiredMixin, View):
    template_name = "nanopore/diagnosis/diagnosis_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(Diagnosis, pk=pk)
        return None

    def get_screening_instance(self):
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

        form = DiagnosisForm(
            instance=obj,
            initial={"screening": screening_instance},
            screening_instance=screening_instance,
        )

        regimen_changes = RegimenChanges.objects.filter(screening=screening_instance)
        regimen_form = RegimenChangesForm()  # <-- create the modal form

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": obj,
                "screening": screening_instance,
                "regimen_changes": regimen_changes,
                "regimen_form": regimen_form,  # <-- pass it to template
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()

        form = DiagnosisForm(
            request.POST, instance=obj, screening_instance=screening_instance
        )

        regimen_changes = RegimenChanges.objects.filter(screening=screening_instance)
        regimen_form = RegimenChangesForm()  # <-- needed if form invalid

        if form.is_valid():
            diagnosis = form.save(commit=False)
            diagnosis.updated_by = request.user
            diagnosis.updated_at = timezone.now()

            if not diagnosis.pk:
                diagnosis.created_by = request.user

            try:
                diagnosis.save()
                form.save_m2m()
            except Exception as e:
                form.add_error(None, str(e))
                return render(
                    request,
                    self.template_name,
                    {
                        "form": form,
                        "object": obj,
                        "screening": screening_instance,
                        "regimen_changes": regimen_changes,
                        "regimen_form": regimen_form,
                    },
                )

            return redirect(self.success_url)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": obj,
                "screening": screening_instance,
                "regimen_changes": regimen_changes,
                "regimen_form": regimen_form,
            },
        )