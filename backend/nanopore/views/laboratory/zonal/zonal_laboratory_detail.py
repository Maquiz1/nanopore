from utils import access
from utils.access_mixins import FormAccessMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import ZonalLaboratory

# -------------------------
# Zonal Laboratory Detail Views
# -------------------------

class ZonalLaboratoryDetailView(FormAccessMixin, DetailView):
    access_form = access.ZONAL_LAB
    model = ZonalLaboratory
    template_name = 'nanopore/laboratory/zonal/zonal_laboratory_detail.html'

