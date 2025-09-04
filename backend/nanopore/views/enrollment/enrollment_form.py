# nanopore/views/enrollment_form.py
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from nanopore.models import Enrollment, Screening
from nanopore.forms.enrollment.enrollmentform import EnrollmentForm

class EnrollmentFormView(LoginRequiredMixin, View):
    template_name = "nanopore/enrollment/enrollment_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")

    def get_object(self):
        """Return Enrollment if pk in URL, else None (new object)."""
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(Enrollment, pk=pk)
        return None

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        initial = {}

        # Pre-fill screening for create
        if not obj:
            screening_id = request.GET.get("screening")
            if screening_id:
                screening = get_object_or_404(Screening, pk=screening_id)
                initial["screening"] = screening

        form = EnrollmentForm(instance=obj, initial=initial)
        form.fields["screening"].disabled = True  # Always read-only

        return render(request, self.template_name, {"form": form, "object": obj})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = EnrollmentForm(request.POST, instance=obj)
        form.fields["screening"].disabled = True

        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.updated_by = request.user
            enrollment.updated_at = timezone.now()

            if not enrollment.pk:  # creating
                enrollment.created_by = request.user
                screening_id = request.GET.get("screening")
                if screening_id:
                    enrollment.screening = get_object_or_404(Screening, pk=screening_id)

            enrollment.save()
            form.save_m2m()
            return redirect(self.success_url)

        return render(request, self.template_name, {"form": form, "object": obj})
