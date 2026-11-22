import logging

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from nanopore.forms.laboratory.zonal.ctrl_isolate_form import CtrlIsolateForm
from nanopore.tasks_tblis_raw import clear_isolate_dst, merge_isolate_from_raw, sync_zonal_laboratory_to_edcs
from nanopore.zonal_rules import CTRL_FIELDS, ctrl_answers, ctrl_records
from utils import access
from utils.access_mixins import FormAccessMixin

logger = logging.getLogger(__name__)


class CtrlIsolateFormView(FormAccessMixin, View):
    """CTRL enters the isolate number of another zone's Zonal Lab form; TB-LIS gives the DST by that number."""
    access_form = access.CTRL_ISOLATES
    access_write = True
    template_name = "nanopore/laboratory/zonal/ctrl_isolate_form.html"

    def get_object(self):
        return get_object_or_404(ctrl_records(self.request.user, write=True), pk=self.kwargs["pk"])

    def next_url(self):
        url = self.request.POST.get("next") or self.request.GET.get("next")
        if url and url_has_allowed_host_and_scheme(url, allowed_hosts={self.request.get_host()}):
            return url
        return reverse("reports:ctrl_isolates")

    def page(self, request, form, obj):
        return render(request, self.template_name, {
            "form": form, "object": obj, "screening": obj.screening, "next": self.next_url(),
            "dst_values": ctrl_answers(obj, CTRL_FIELDS[1:]),
        })

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return self.page(request, CtrlIsolateForm(instance=obj), obj)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        old_number = obj.isolate_unique_lab_no  # validating the form changes obj
        form = CtrlIsolateForm(request.POST, instance=obj)
        if not form.is_valid():
            return self.page(request, form, obj)
        record = form.save(commit=False)
        record.updated_by = request.user
        record.updated_at = timezone.now()
        with transaction.atomic():
            if old_number and old_number != record.isolate_unique_lab_no:
                clear_isolate_dst(record, old_number)
            record.save()
            found = merge_isolate_from_raw(record)
        try:
            with transaction.atomic():  # EDCS/TBLIS and the exports mustn't keep the old number's DST until tonight
                sync_zonal_laboratory_to_edcs(record)
        except Exception:  # the daily sync tries again
            logger.exception("Could not sync Zonal Lab %s to EDCS/TBLIS", record.pk)
        if found:
            messages.success(request, f"Isolate number saved for {obj.screening.pid}; DST added from TB-LIS.")
        else:
            messages.success(request, f"Isolate number saved for {obj.screening.pid}; DST comes with a TB-LIS upload that has this number.")
        return redirect(self.next_url())
