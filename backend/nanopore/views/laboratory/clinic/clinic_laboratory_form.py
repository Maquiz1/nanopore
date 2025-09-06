# nanopore/views/laboratory/clinic/clinic_laboratory_form_views.py
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from nanopore.models import ClinicLaboratory, Screening
from nanopore.forms.laboratory.clinic.cliniclabform import ClinicLaboratoryForm


class ClinicLaboratoryFormView(LoginRequiredMixin, View):
    template_name = "nanopore/laboratory/clinic/clinic_laboratory_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(ClinicLaboratory, pk=pk)
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
        form = ClinicLaboratoryForm(instance=obj, initial={"screening": screening_instance})
        return render(
            request,
            self.template_name,
            {"form": form, "object": obj, "screening": screening_instance},
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()

        # Pass screening_instance to the form
        if obj:
            form = ClinicLaboratoryForm(request.POST, instance=obj)
        else:
            form = ClinicLaboratoryForm(request.POST, initial={"screening": screening_instance})

        if form.is_valid():
            lab = form.save(commit=False)
            lab.updated_by = request.user
            lab.updated_at = timezone.now()

            if not lab.pk:  # create
                lab.created_by = request.user
                lab.screening = screening_instance  # assign manually

            lab.save()
            form.save_m2m()
            return redirect(self.success_url)

        return render(
            request,
            self.template_name,
            {"form": form, "object": obj, "screening": screening_instance},
        )


