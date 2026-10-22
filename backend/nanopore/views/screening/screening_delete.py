from utils import access
from utils.access_mixins import SoftDeleteMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Screening Views
# -------------------------


class ScreeningDeleteView(SoftDeleteMixin, DeleteView):
    access_form = access.SCREENING
    access_site_field = "site"
    model = Screening
    success_url = reverse_lazy('nanopore:form-status-list')
