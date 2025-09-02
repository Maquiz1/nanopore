from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import Screening
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Screening Views
# -------------------------


class ScreeningDeleteView(LoginRequiredMixin, DeleteView):
    model = Screening
    template_name = 'nanopore/screening/screening_confirm_delete.html'
    success_url = reverse_lazy('nanopore:screening-list')
