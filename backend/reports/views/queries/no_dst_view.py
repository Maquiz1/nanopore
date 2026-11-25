"""Positive culture, no DST (reports/services/no_dst.py): information for the study team, not queries."""
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.views import View

from django.utils.http import urlencode

from reports.services.no_dst import GROUPS, no_dst_counts, no_dst_records, zones_and_sites
from utils import access
from utils.access_mixins import FeatureAccessMixin


class NoDstView(FeatureAccessMixin, View):
    access_feature = access.TBLIS_FOLLOW_UP  # the same people as TB-LIS follow-up
    template_name = "reports/data_quality/no_dst.html"
    paginate_by = 50

    def get(self, request):
        group = request.GET.get("group") if request.GET.get("group") in dict(GROUPS) else "dar"
        search = request.GET.get("q", "").strip()
        zones, sites = zones_and_sites(request.user)
        pick = lambda key, allowed: int(request.GET[key]) if request.GET.get(key, "").isdigit() and int(request.GET[key]) in allowed else None
        zone_id, site_id = pick("zone", zones), pick("site", sites)
        show_accepted = request.GET.get("show") == "accepted"
        records = no_dst_records(request.user, group, zone_id, site_id, accepted=show_accepted).select_related(
            "screening__site__district__region__zone", "lj_results", "mgit_results")
        if search:
            records = records.filter(Q(screening__pid__icontains=search) | Q(unique_lab_no__icontains=search))
        counts = no_dst_counts(request.user, zone_id, site_id)
        page = Paginator(records, self.paginate_by).get_page(request.GET.get("page"))
        from reports.services.accepted import NO_DST, holding, lapsed
        from reports.services.no_dst import no_dst_values
        on_page = list(page.object_list)
        found = holding(NO_DST, group, on_page, no_dst_values) if show_accepted else {}
        changed = set() if show_accepted else lapsed(NO_DST, group, on_page, no_dst_values)
        for obj in on_page:
            obj.accepted_item, obj.accept_lapsed = found.get(str(obj.pk)), str(obj.pk) in changed
        base = {k: v for k, v in (("group", group), ("zone", zone_id), ("site", site_id), ("q", search)) if v}
        return render(request, self.template_name, {
            "show_accepted": show_accepted, "accept_base": urlencode(base),
            "accepted_total": no_dst_records(request.user, group, zone_id, site_id, accepted=True).count(),
            "groups": [{"key": key, "label": label, "count": counts[key]} for key, label in GROUPS],
            "group": group, "page_obj": page, "search": search,
            "zones": zones, "sites": sites, "selected_zone": zone_id, "selected_site": site_id,
            "filter_query": urlencode({k: v for k, v in (("zone", zone_id), ("site", site_id), ("q", search)) if v}),
        })
