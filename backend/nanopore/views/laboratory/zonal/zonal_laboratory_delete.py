from utils import access
from utils.access_mixins import SoftDeleteMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import ZonalLaboratory
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Zonal Laboratory Views
# -------------------------


class ZonalLaboratoryDeleteView(SoftDeleteMixin, DeleteView):
    access_form = access.ZONAL_LAB
    model = ZonalLaboratory
    success_url = reverse_lazy('nanopore:form-status-list')
