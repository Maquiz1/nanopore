from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from nanopore.models import ClinicLaboratory
from nanopore.forms.laboratory.clinic.cliniclabform import ClinicLaboratoryForm

class ClinicLaboratoryCreateView(LoginRequiredMixin, CreateView):
    model = ClinicLaboratory
    form_class = ClinicLaboratoryForm
    template_name = "nanopore/laboratory/clinic/cliniclab_form.html"
    success_url = reverse_lazy("nanopore:cliniclab-list")

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Track creator and updater
        obj.created_by = self.request.user
        obj.updated_by = self.request.user
        obj.updated_at = timezone.now()

        try:
            obj.save()
            form.save_m2m()
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return redirect(self.success_url)
