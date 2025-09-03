from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect

from nanopore.models import ClinicLaboratory
from nanopore.forms.laboratory.clinic.cliniclabform import ClinicLaboratoryForm  # adjust path

class ClinicLaboratoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ClinicLaboratory
    form_class = ClinicLaboratoryForm
    template_name = "nanopore/laboratory/clinic/clinic_laboratory_form.html"
    success_url = reverse_lazy("nanopore:clinic-laboratory-list")

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Update audit fields
        obj.updated_by = self.request.user
        obj.updated_at = timezone.now()

        # Optional validation: test_date cannot be before screening date
        if obj.test_date < obj.screening.screening_date:
            form.add_error("test_date", "Test date cannot be before screening date.")
            return self.form_invalid(form)

        try:
            obj.save()
            form.save_m2m()
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return redirect(self.success_url)
