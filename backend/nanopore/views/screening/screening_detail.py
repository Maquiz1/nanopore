from utils import access
from utils.access_mixins import FormAccessMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Screening Views
# -------------------------

class ScreeningDetailView(FormAccessMixin, DetailView):
    access_form = access.SCREENING
    access_site_field = "site"
    model = Screening
    template_name = 'nanopore/screening/screening_detail.html'

