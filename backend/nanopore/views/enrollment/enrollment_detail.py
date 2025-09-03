from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import Enrollment
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Enrollment Detail Views
# -------------------------

class EnrollmentDetailView(LoginRequiredMixin, DetailView):
    model = Enrollment
    template_name = 'nanopore/enrollment/enrollment_detail.html'

