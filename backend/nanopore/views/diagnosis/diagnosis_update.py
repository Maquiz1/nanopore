from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect

from nanopore.models import Diagnosis
from nanopore.forms.diagnosis.diagnosisform import DiagnosisForm


class DiagnosisUpdateView(LoginRequiredMixin, UpdateView):
    model = Diagnosis
    form_class = DiagnosisForm
    template_name = "nanopore/diagnosis/diagnosis_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Update audit fields
        obj.updated_by = self.request.user
        obj.updated_at = timezone.now()

        # Optional: add custom logic here
        # Example: ensure diagnosis date is not before screening date
        if obj.diagnosis_date < obj.screening.screening_date:
            form.add_error("diagnosis_date", "Diagnosis date cannot be before screening date.")
            return self.form_invalid(form)

        try:
            obj.save()
            form.save_m2m()
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return redirect(self.success_url)
