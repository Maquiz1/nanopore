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
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(Enrollment, pk=pk)
        return None

    def get_screening_instance(self):
        if self.get_object():  # updating
            return self.get_object().screening
        screening_id = self.request.GET.get("screening")
        if screening_id:
            return get_object_or_404(Screening, pk=screening_id)
        return None

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()
        form = EnrollmentForm(instance=obj, screening_instance=screening_instance)
        return render(request, self.template_name, {"form": form, "object": obj})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()
        form = EnrollmentForm(request.POST, instance=obj, screening_instance=screening_instance)

        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.updated_by = request.user
            enrollment.updated_at = timezone.now()

            if not enrollment.pk:
                enrollment.created_by = request.user
                enrollment.screening = screening_instance  # assign manually

            enrollment.save()
            form.save_m2m()
            return redirect(self.success_url)

        return render(request, self.template_name, {"form": form, "object": obj})
