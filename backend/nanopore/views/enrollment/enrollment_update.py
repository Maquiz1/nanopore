# nanopore/views/enrollment_create.py
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from nanopore.models import Enrollment, Screening
from nanopore.forms.enrollment.enrollmentform import EnrollmentForm


class EnrollmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = "nanopore/enrollment/enrollment_form.html"
    success_url = reverse_lazy("nanopore:enrollment-list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["screening"].disabled = True
        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updated_by = self.request.user
        obj.updated_at = timezone.now()
        obj.save()
        return redirect(self.success_url)
