from urllib.parse import parse_qsl, urlencode

from django.http import HttpResponseNotAllowed

from nanopore.zonal_sections import BY_KEY, by_section
from nanopore.substudy4_set_aside import may_start_for
import logging

from django.db import transaction

from nanopore.tasks_tblis_raw import sync_with_latest_tblis
from utils import access
from utils.access_mixins import FormAccessMixin
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect

from nanopore.models import ZonalLaboratory
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm  # adjust path

from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy

from nanopore.models import ZonalLaboratory, Screening
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages

logger = logging.getLogger(__name__)


class ZonalLabFormView(FormAccessMixin, View):
    access_form = access.ZONAL_LAB
    access_is_form = True
    template_name = "nanopore/laboratory/zonal/zonal_laboratory_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")
    view_only = False  # the View button: the whole form, greyed out, whatever the user may change

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(self.scope(ZonalLaboratory.objects.all()), pk=pk)
        return None

    def get_screening_instance(self):
        obj = self.get_object()
        if obj:
            return obj.screening
        screening_id = self.request.GET.get("screening")
        if screening_id:
            return get_object_or_404(self.scope(Screening.objects.all(), "site"), pk=screening_id)
        return None

    def by_section_redirect(self, request, obj):
        """System Controls "Zonal Lab by section": Edit opens the sections; ?all=1 keeps the full form."""
        if self.view_only or request.GET.get("all") == "1" or not by_section():
            return None
        keep = urlencode({k: request.GET[k] for k in ("next",) if request.GET.get(k)})
        if obj is not None:
            section = BY_KEY.get(request.GET.get("section"))
            url = (reverse("nanopore:zonal-lab-section", args=[obj.pk, section.key]) if section
                   else reverse("nanopore:zonal-lab-hub", args=[obj.pk]))
            return redirect(url + (f"?{keep}" if keep else ""))
        screening_id = request.GET.get("screening")
        if screening_id:
            return redirect(reverse("nanopore:zonal-lab-section-new", args=["reception"])
                            + "?" + urlencode({"screening": screening_id, **dict(parse_qsl(keep))}))
        return None  # no participant chosen yet: the full form picks one

    def refuse_substudy4(self, request, obj):
        """The Zonal Lab follows Substudy 2: no new form for a Substudy 4 participant (nanopore/substudy4_set_aside.py)."""
        if obj is not None:
            return None
        screening = self.get_screening_instance()
        if screening is not None and not may_start_for(request.user, screening):
            messages.info(request, f"{screening.pid} is Substudy 4: the Zonal Lab is not entered for Substudy 4.")
            return redirect("nanopore:form-status-list")
        return None

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        moved = self.by_section_redirect(request, obj)
        if moved:
            return moved
        refused = self.refuse_substudy4(request, obj)
        if refused:
            return refused
        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")

        screening_instance = self.get_screening_instance()

        form = ZonalLaboratoryForm(
            instance=obj,
            initial={"screening": screening_instance},
            screening_instance=screening_instance
        )
        read_only = self.view_only or self.is_read_only(obj)
        if read_only:
            for field in form.fields.values():
                field.disabled = True

        return render(
            request,
            self.template_name,
            {"form": form, "object": obj, "screening": screening_instance, "next": next_url, "read_only": read_only,
             "edit_link": getattr(request, "view_edit_url", None)}
        )

    def post(self, request, *args, **kwargs):
        if self.view_only:
            return HttpResponseNotAllowed(["GET"])
        obj = self.get_object()
        refused = self.refuse_substudy4(request, obj)
        if refused:
            return refused
        screening_instance = self.get_screening_instance()

        form = ZonalLaboratoryForm(
            request.POST,
            instance=obj,
            screening_instance=screening_instance
        )

        self.limit_choices(form)

        if form.is_valid():
            zonal_lab = form.save(commit=False)
            zonal_lab.updated_by = request.user
            zonal_lab.updated_at = timezone.now()

            if not zonal_lab.pk:
                zonal_lab.created_by = request.user
                zonal_lab.screening = screening_instance

            try:
                form.apply_change_reason(zonal_lab).save()
                form.save_m2m()
            except Exception as e:
                form.add_error(None, str(e))
                return render(
                    request,
                    self.template_name,
                    {"form": form, "object": obj, "screening": screening_instance}
                )

            try:
                with transaction.atomic():
                    sync_with_latest_tblis(zonal_lab)
            except Exception:  # the nightly sync tries again
                logger.exception("Could not sync Zonal Lab %s to EDCS/TBLIS", zonal_lab.pk)

            messages.success(request, "Zonal Lab saved successfully.")

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
