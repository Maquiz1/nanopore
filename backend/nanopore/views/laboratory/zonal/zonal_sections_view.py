"""The Zonal Lab section hub and its section forms (nanopore/zonal_sections.py)."""
import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from nanopore import history
from nanopore.forms.laboratory.zonal.section_forms import SECTION_FORMS
from nanopore.models import Screening, ZonalLaboratory
from nanopore.tasks_tblis_raw import sync_with_latest_tblis
from nanopore.zonal_sections import BY_KEY, DAR_CTRL_FORMS, section_cards
from nanopore.zonal_rules import is_lab_number_only
from nanopore.substudy4_set_aside import may_start_for
from utils import access
from utils.access_mixins import FormAccessMixin

logger = logging.getLogger(__name__)

EDIT_ALL_ROLES = (access.ADMIN, access.DATA_MANAGER, access.DATA_SPECIALIST)


def can_edit_all(user):
    """Back-entry of a whole paper form at once stays with the data team."""
    return user.is_superuser or access.has_role(user, *EDIT_ALL_ROLES)


def hub_url(record):
    return reverse("nanopore:zonal-lab-hub", args=[record.pk])


class ZonalLabHubView(FormAccessMixin, View):
    """One participant's Zonal Lab, section by section, with where each one stands."""
    access_form = access.ZONAL_LAB
    template_name = "nanopore/laboratory/zonal/zonal_lab_hub.html"

    def get(self, request, pk):
        record = get_object_or_404(self.scope(ZonalLaboratory.objects.select_related("screening__site")), pk=pk)
        return render(request, self.template_name, {
            "object": record, "screening": record.screening,
            "cards": section_cards(record, record.screening),
            "can_edit": not self.is_read_only(record),
            "edit_all": not self.is_read_only(record) and can_edit_all(request.user),
        })


class ZonalLabSectionView(FormAccessMixin, View):
    """One section of the Zonal Lab form. Sample reception also starts a new record."""
    access_form = access.ZONAL_LAB
    access_is_form = True
    template_name = "nanopore/laboratory/zonal/zonal_lab_section.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.section = BY_KEY.get(kwargs.get("section"))
        if self.section is None or self.section.key not in SECTION_FORMS:
            raise Http404("This section has no form of its own yet.")
        self.form_class = SECTION_FORMS[self.section.key]

    def get_record_and_screening(self):
        pk = self.kwargs.get("pk")
        if pk:
            record = get_object_or_404(self.scope(ZonalLaboratory.objects.select_related("screening__site")), pk=pk)
            return record, record.screening
        if self.section.key != "reception":
            raise Http404("A Zonal Lab record starts with sample reception.")
        screening_id = self.request.GET.get("screening") or self.request.POST.get("screening")
        screening = get_object_or_404(self.scope(Screening.objects.all(), "site"), pk=screening_id)
        if not hasattr(screening, "zonal_laboratory") and not may_start_for(self.request.user, screening):
            raise PermissionDenied(f"{screening.pid} is Substudy 4: the Zonal Lab is not entered for Substudy 4.")
        return None, screening

    def page(self, form, record, screening, read_only):
        if read_only:
            for form_field in form.fields.values():
                form_field.disabled = True
        return render(self.request, self.template_name, {
            "form": form, "object": record, "screening": screening, "section": self.section,
            "read_only": read_only, "back": self.next_url() or (hub_url(record) if record else reverse("nanopore:form-status-list")),
            "next": self.next_url() or "",
        })

    def next_url(self):
        """Where the user came from (a query list), to go back to after saving."""
        url = self.request.POST.get("next") or self.request.GET.get("next")
        if url and url_has_allowed_host_and_scheme(url, allowed_hosts={self.request.get_host()}):
            return url
        return None

    def dar_elsewhere(self, record, screening):
        """Dar es Salaam: only the lab number is entered here; the rest is TB-LIS's or CTRL's."""
        if self.section.key == "reception" or not is_lab_number_only(screening):
            return None
        if record is not None and self.section.key in DAR_CTRL_FORMS:
            return redirect(reverse(DAR_CTRL_FORMS[self.section.key], args=[record.pk]))
        messages.info(self.request, f"Dar es Salaam: {self.section.title} comes from TB-LIS (see the EDCS/TBLIS record).")
        return redirect(hub_url(record)) if record else redirect(reverse("nanopore:form-status-list"))

    def get(self, request, *args, **kwargs):
        record, screening = self.get_record_and_screening()
        elsewhere = self.dar_elsewhere(record, screening)
        if elsewhere:
            return elsewhere
        existing = getattr(screening, "zonal_laboratory", None) if record is None else None
        if existing:  # already started: open it instead of a second record
            return redirect(reverse("nanopore:zonal-lab-section", args=[existing.pk, self.section.key]))
        form = self.form_class(instance=record, screening=screening)
        viewing = record is not None and self.request.GET.get("view") == "1"  # the card's View button
        return self.page(form, record, screening, record is not None and (viewing or self.is_read_only(record)))

    def post(self, request, *args, **kwargs):
        record, screening = self.get_record_and_screening()
        if record is not None and self.is_read_only(record):
            raise PermissionDenied
        if record is None and hasattr(screening, "zonal_laboratory"):
            messages.error(request, f"{screening.pid} already has a Zonal Lab record.")
            return redirect(hub_url(screening.zonal_laboratory))
        elsewhere = self.dar_elsewhere(record, screening)
        if elsewhere:
            return elsewhere
        form = self.form_class(request.POST, instance=record, screening=screening)
        if not form.has_answers:
            return redirect(hub_url(record))
        if not form.is_valid():
            return self.page(form, record, screening, False)

        saved = form.save(commit=False)
        saved.updated_by = request.user
        saved.updated_at = timezone.now()
        if saved.pk is None:
            saved.created_by = request.user
            saved.screening = screening
        source = f"Zonal Lab: {self.section.title}"
        with history.source(source):
            form.apply_change_reason(saved).save()
            form.save_m2m()
        try:
            with transaction.atomic(), history.source(source):
                sync_with_latest_tblis(saved)
        except Exception:  # the nightly sync tries again
            logger.exception("Could not sync Zonal Lab %s to EDCS/TBLIS", saved.pk)
        messages.success(request, f"{self.section.title} saved for {screening.pid}.")
        return redirect(self.next_url() or hub_url(saved))
