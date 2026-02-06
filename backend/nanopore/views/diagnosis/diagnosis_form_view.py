from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages

from nanopore.models import Diagnosis, Screening, RegimenChanges
from nanopore.forms.diagnosis.diagnosisform import DiagnosisForm
from nanopore.forms.regimen.regimenform import RegimenChangesForm
from django.utils.http import url_has_allowed_host_and_scheme


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

    def get_regimen_error(self, diagnosis, screening_instance):
        """
        Returns a message to display inside the Regimen Changes table:
        - If regimen_changed = Yes (id=1) and no changes exist → "Regimen changes are missing"
        - If regimen_changed = No (id !=1) → "N/A"
        - Else → None
        """
        regimen_changes = RegimenChanges.objects.filter(screening=screening_instance)

        if diagnosis and diagnosis.regimen_changed:
            if diagnosis.regimen_changed.id == 1 and not regimen_changes.exists():
                return "Regimen changes are missing"
            elif diagnosis.regimen_changed.id != 1:
                return "N/A"
        return None

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")

        screening_instance = self.get_screening_instance()

        form = DiagnosisForm(
            instance=obj,
            screening_instance=screening_instance,
        )

        regimen_changes = RegimenChanges.objects.filter(screening=screening_instance)
        regimen_form = RegimenChangesForm()  # For modal
        regimen_error = self.get_regimen_error(obj, screening_instance)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": obj,
                "screening": screening_instance,
                "regimen_changes": regimen_changes,
                "regimen_form": regimen_form,
                "regimen_error": regimen_error,
                "next": next_url,
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()

        form = DiagnosisForm(
            request.POST, instance=obj, screening_instance=screening_instance
        )

        regimen_changes = RegimenChanges.objects.filter(screening=screening_instance)
        regimen_form = RegimenChangesForm()  # For modal if needed

        # Compute regimen error for template
        regimen_error = self.get_regimen_error(obj, screening_instance)

        if form.is_valid():
            diagnosis = form.save(commit=False)
            diagnosis.updated_by = request.user
            diagnosis.updated_at = timezone.now()
            if not diagnosis.pk:
                diagnosis.created_by = request.user

            diagnosis.save()
            form.save_m2m()
            messages.success(request, "Diagnosis saved successfully!")
            # return redirect(self.success_url)
            next_url = request.POST.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": obj,
                "screening": screening_instance,
                "regimen_changes": regimen_changes,
                "regimen_form": regimen_form,
                "regimen_error": regimen_error,
            },
        )
