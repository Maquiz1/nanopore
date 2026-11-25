"""Nanopore failed (reports/services/nanopore_failed.py): information for the team, not queries."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views import View

from nanopore import history
from nanopore.models import ZonalLaboratory
from nanopore.zonal_rules import is_lab_number_only
from reports.services.nanopore_failed import TABS, may_close, nanopore_failed_counts, nanopore_failed_records, zones_and_sites
from utils import access
from utils.access_mixins import FeatureAccessMixin


class NanoporeFailedView(FeatureAccessMixin, View):
    access_feature = access.TBLIS_FOLLOW_UP  # the same people as No DST and TB-LIS follow-up
    template_name = "reports/data_quality/nanopore_failed.html"
    paginate_by = 50

    def get(self, request):
        tab = request.GET.get("tab") if request.GET.get("tab") in dict(TABS) else "since"
        search = request.GET.get("q", "").strip()
        zones, sites = zones_and_sites(request.user)
        pick = lambda key, allowed: int(request.GET[key]) if request.GET.get(key, "").isdigit() and int(request.GET[key]) in allowed else None
        zone_id, site_id = pick("zone", zones), pick("site", sites)
        records = nanopore_failed_records(request.user, tab, zone_id, site_id)
        if search:
            records = records.filter(Q(screening__pid__icontains=search) | Q(unique_lab_no__icontains=search))
        counts = nanopore_failed_counts(request.user, zone_id, site_id)
        page = Paginator(records, self.paginate_by).get_page(request.GET.get("page"))
        today = timezone.localdate()
        rows = []
        for lab in page:
            dar = is_lab_number_only(lab.screening)
            rows.append({
                "lab": lab, "last": lab.nanopore_runs.order_by("-run_date", "-pk").first(),
                "days": (today - lab.last_run).days if lab.last_run else None,
                "view": (reverse("nanopore:ctrl-dar-nanopore", args=[lab.pk]) if dar
                         else reverse("nanopore:zonal-lab-section", args=[lab.pk, "nanopore"])) + "?view=1",
                "may_close": may_close(request.user, lab),
            })
        return render(request, self.template_name, {
            "rows": rows, "page_obj": page, "search": search, "tab": tab,
            "zones": zones, "sites": sites, "selected_zone": zone_id, "selected_site": site_id,
            "filter_query": urlencode({k: v for k, v in (("zone", zone_id), ("site", site_id), ("q", search)) if v}),
            "tabs": [{"key": key, "label": label, "count": counts[key]} for key, label in TABS],
        })

    def post(self, request):
        """No re-run planned (with the reason), or undo it: kept in the record's history."""
        lab = get_object_or_404(ZonalLaboratory, pk=request.POST.get("lab"))
        if not may_close(request.user, lab):
            raise PermissionDenied
        undo = request.POST.get("action") == "reopen"
        reason = (request.POST.get("reason") or "").strip()
        if not undo and not reason:
            messages.error(request, f"{lab.screening.pid}: say why no re-run is planned.")
        else:
            lab.nanopore_rerun_not_planned = not undo
            lab.nanopore_rerun_not_planned_reason = "" if undo else reason
            lab.updated_by = request.user
            lab._change_reason = "Re-run planned again" if undo else f"No re-run planned: {reason}"
            with history.source("Nanopore failed list"):
                lab.save()
            messages.success(request, f"{lab.screening.pid}: {'back on the list' if undo else 'no re-run planned'}.")
        back = request.POST.get("back") or ""
        if not url_has_allowed_host_and_scheme(back, allowed_hosts={request.get_host()}):
            back = reverse("reports:nanopore_failed")
        return redirect(back)
