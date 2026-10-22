from utils import access
from utils.access_mixins import FormAccessMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import ClinicLaboratory

# -------------------------
# Clinic Laboratory Detail Views
# -------------------------

class ClinicLaboratoryDetailView(FormAccessMixin, DetailView):
    access_form = access.CLINIC_LAB
    model = ClinicLaboratory
    template_name = 'nanopore/laboratory/clinic/clinic_laboratory_detail.html'

