from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import ClinicLaboratory

# -------------------------
# Clinic Laboratory Detail Views
# -------------------------

class ClinicLaboratoryDetailView(LoginRequiredMixin, DetailView):
    model = ClinicLaboratory
    template_name = 'nanopore/laboratory/clinic/clinic_lab_detail.html'

