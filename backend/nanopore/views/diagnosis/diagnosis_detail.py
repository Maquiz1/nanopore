from utils import access
from utils.access_mixins import FormAccessMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import Diagnosis
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Diagnosis Detail Views
# -------------------------

class DiagnosisDetailView(FormAccessMixin, DetailView):
    access_form = access.DIAGNOSIS
    model = Diagnosis
    template_name = 'nanopore/diagnosis/diagnosis_detail.html'
