from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect

from nanopore.models import ZonalLaboratory
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm  # adjust path

from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from nanopore.models import ZonalLaboratory, Screening
from django.utils.http import url_has_allowed_host_and_scheme

class ZonalLabFormView(LoginRequiredMixin, View):
    template_name = "nanopore/laboratory/zonal/zonal_laboratory_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(ZonalLaboratory, pk=pk)
        return None

    def get_screening_instance(self):
        obj = self.get_object()
        if obj:
            return obj.screening
        screening_id = self.request.GET.get("screening")
        if screening_id:
            return get_object_or_404(Screening, pk=screening_id)
        return None

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")

        screening_instance = self.get_screening_instance()

        form = ZonalLaboratoryForm(
            instance=obj,
            initial={"screening": screening_instance},
            screening_instance=screening_instance
        )

        return render(
            request,
            self.template_name,
            {"form": form, "object": obj, "screening": screening_instance, "next": next_url}
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        screening_instance = self.get_screening_instance()

        form = ZonalLaboratoryForm(
            request.POST,
            instance=obj,
            screening_instance=screening_instance
        )

        if form.is_valid():
            zonal_lab = form.save(commit=False)
            zonal_lab.updated_by = request.user
            zonal_lab.updated_at = timezone.now()

            if not zonal_lab.pk:
                zonal_lab.created_by = request.user
                zonal_lab.screening = screening_instance

            try:
                zonal_lab.save()
                form.save_m2m()
            except Exception as e:
                form.add_error(None, str(e))
                return render(
                    request,
                    self.template_name,
                    {"form": form, "object": obj, "screening": screening_instance}
                )

            # return redirect(self.success_url)
            next_url = request.POST.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)

        return render(
            request,
            self.template_name,
            {"form": form, "object": obj, "screening": screening_instance}
        )
