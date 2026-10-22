from utils import access
from utils.access_mixins import FormAccessMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from nanopore.models import Enrollment
from nanopore.forms.screening.screeningform import ScreeningForm

# -------------------------
# Enrollment Detail Views
# -------------------------

class EnrollmentDetailView(FormAccessMixin, DetailView):
    access_form = access.ENROLLMENT
    model = Enrollment
    template_name = 'nanopore/enrollment/enrollment_detail.html'

