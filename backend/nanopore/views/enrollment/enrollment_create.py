# nanopore/views/enrollment_create.py
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from nanopore.models import Enrollment, Screening
from nanopore.forms.enrollment.enrollmentform import EnrollmentForm


class EnrollmentCreateView(LoginRequiredMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = "nanopore/enrollment/enrollment_form.html"
    success_url = reverse_lazy("nanopore:enrollment-list")

    def get_initial(self):
        initial = super().get_initial()
        screening_id = self.request.GET.get("screening")
        if screening_id:
            screening = get_object_or_404(Screening, pk=screening_id)
            initial["screening"] = screening
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # screening always readonly
        form.fields["screening"].disabled = True
        return form

    def form_valid(self, form):
        obj = form.save(commit=False)

        # Assign created_by / updated_by
        obj.created_by = self.request.user
        obj.updated_by = self.request.user
        obj.updated_at = timezone.now()

        # attach screening explicitly
        if not obj.screening_id:
            screening_id = self.request.GET.get("screening")
            obj.screening = get_object_or_404(Screening, pk=screening_id)

        try:
            obj.save()
            form.save_m2m()
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return redirect(self.success_url)

