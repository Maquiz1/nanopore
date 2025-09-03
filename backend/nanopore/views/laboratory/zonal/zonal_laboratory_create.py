from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from nanopore.models import ZonalLaboratory
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.models import Enrollment, ClinicLaboratory, Diagnosis, ZonalLaboratory

class ZonalLaboratoryCreateView(LoginRequiredMixin, CreateView):
    model = ZonalLaboratory
    form_class = ZonalLaboratoryForm
    template_name = "nanopore/laboratory/zonal/zonal_laboratory_form.html"
    success_url = reverse_lazy("nanopore:zonal-laboratory-list")

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
