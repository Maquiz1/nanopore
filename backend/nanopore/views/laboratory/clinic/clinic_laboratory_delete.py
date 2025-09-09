from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import ClinicLaboratory
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Screening Views
# -------------------------


class ClinicLaboratoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ClinicLaboratory
    template_name = 'nanopore/laboratory/clinic/clinic_laboratory_confirm_delete.html'
    success_url = reverse_lazy('nanopore:form-status-list')
