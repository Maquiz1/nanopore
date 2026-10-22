from utils import access
from utils.access_mixins import SoftDeleteMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import ClinicLaboratory
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Screening Views
# -------------------------


class ClinicLaboratoryDeleteView(SoftDeleteMixin, DeleteView):
    access_form = access.CLINIC_LAB
    model = ClinicLaboratory
    success_url = reverse_lazy('nanopore:form-status-list')
