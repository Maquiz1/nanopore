import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from nanopore.forms.laboratory.zonal.ctrl_dar_forms import DarLpaForm, DarNanoporeForm
from nanopore.tasks_tblis_raw import sync_with_latest_tblis
from nanopore.zonal_rules import ctrl_dar_records
from utils import access
from utils.access_mixins import FormAccessMixin

logger = logging.getLogger(__name__)


class CtrlDarFormView(FormAccessMixin, View):
    """One of CTRL's Dar es Salaam forms. Saving updates the EDCS/TBLIS record at once, so its queries close."""
    access_form = access.CTRL_ISOLATES
    template_name = "nanopore/laboratory/zonal/ctrl_dar_form.html"
    form_class = None
    section = None
    title = None

    def get_object(self):
        return get_object_or_404(ctrl_dar_records(self.request.user), pk=self.kwargs["pk"])

    def next_url(self):
        url = self.request.POST.get("next") or self.request.GET.get("next")
        if url and url_has_allowed_host_and_scheme(url, allowed_hosts={self.request.get_host()}):
            return url
        return reverse("reports:ctrl_dar_work") + f"?tab={self.section}"

    def page(self, request, form, obj):
        return render(request, self.template_name, {
            "form": form, "object": obj, "screening": obj.screening, "next": self.next_url(),
            "section": self.section, "title": self.title,
        })

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        return self.page(request, self.form_class(instance=obj), obj)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = self.form_class(request.POST, instance=obj)
        if not form.is_valid():
            return self.page(request, form, obj)
        record = form.save(commit=False)
        record.updated_by = request.user
        record.updated_at = timezone.now()
        record.save()
        form.save_m2m()
        try:
            sync_with_latest_tblis(record)
        except Exception:  # the daily sync tries again
            logger.exception("Could not sync Zonal Lab %s to EDCS/TBLIS", record.pk)
        messages.success(request, f"{self.title} saved for {obj.screening.pid}.")
        return redirect(self.next_url())


class CtrlDarNanoporeView(CtrlDarFormView):
    form_class, section, title = DarNanoporeForm, "nanopore", "Nanopore sequencing"


class CtrlDarLpaView(CtrlDarFormView):
    form_class, section, title = DarLpaForm, "lpa", "Line probe assay checkboxes"
