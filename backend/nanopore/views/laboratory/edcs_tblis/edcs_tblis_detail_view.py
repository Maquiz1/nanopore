from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import ZonalLaboratory

# -------------------------
# Zonal Laboratory Detail Views
# -------------------------

class ZonalLaboratoryDetailView(LoginRequiredMixin, DetailView):
    model = ZonalLaboratory
    template_name = 'nanopore/laboratory/zonal/zonal_laboratory_detail.html'

