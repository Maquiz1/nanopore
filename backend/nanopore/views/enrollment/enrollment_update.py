from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect

from nanopore.models import Enrollment
from nanopore.forms.enrollment.enrollmentform import EnrollmentForm


class EnrollmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = "nanopore/enrollment/enrollment_form.html"
    success_url = reverse_lazy("nanopore:enrollment-list")

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Update audit fields
        obj.updated_by = self.request.user
        obj.updated_at = timezone.now()

        # You can add any extra logic here, e.g., recalculation, validation
        # Example: make sure enrollment date is not before screening date
        if obj.enrollment_date < obj.screening.screening_date:
            form.add_error("enrollment_date", "Enrollment date cannot be before screening date.")
            return self.form_invalid(form)

        try:
            obj.save()
            form.save_m2m()
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return redirect(self.success_url)
