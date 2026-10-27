from utils import access
from utils.access_mixins import FormAccessMixin
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


class DiagnosisFormView(FormAccessMixin, View):
    access_form = access.DIAGNOSIS
    access_is_form = True
    template_name = "nanopore/diagnosis/diagnosis_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(self.scope(Diagnosis.objects.all()), pk=pk)
        return None

    def get_screening_instance(self):
        obj = self.get_object()
        if obj:
            return obj.screening
        screening_id = self.request.GET.get("screening")
        if screening_id:
            return get_object_or_404(self.scope(Screening.objects.all(), "site"), pk=screening_id)
        return None

    def get_regimen_changes(self, screening_instance):
        # Always listed, whatever 10(a) says, so a mismatch can be seen and fixed
        if not screening_instance:
            return RegimenChanges.objects.none()
        return RegimenChanges.objects.filter(screening=screening_instance).select_related("changes", "reason").order_by("date", "pk")

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")

        screening_instance = self.get_screening_instance()

        form = DiagnosisForm(
            instance=obj,
            screening_instance=screening_instance,
        )

        regimen_changes = self.get_regimen_changes(screening_instance)
        regimen_form = RegimenChangesForm()  # For modal

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": obj,
                "screening": screening_instance,
                "regimen_changes": regimen_changes,
                "regimen_form": regimen_form,
                "next": next_url,
            },
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()

        form = DiagnosisForm(
            request.POST, instance=obj, screening_instance=screening_instance
        )

        regimen_changes = self.get_regimen_changes(screening_instance)
        regimen_form = RegimenChangesForm()  # For modal if needed

        self.limit_choices(form)

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
                "next": request.POST.get("next"),
            },
        )
