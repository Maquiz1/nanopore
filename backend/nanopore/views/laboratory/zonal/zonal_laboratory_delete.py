from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import ZonalLaboratory
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Zonal Laboratory Views
# -------------------------


class ZonalLaboratoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ZonalLaboratory
    template_name = 'nanopore/laboratory/zonal/zonal_laboratory_confirm_delete.html'
    success_url = reverse_lazy('nanopore:form-status-list')
