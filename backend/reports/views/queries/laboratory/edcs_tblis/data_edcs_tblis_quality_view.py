# reports/views/queries/laboratory/zonal/data_zonal_quality_view.py

from utils import access
from utils.access_mixins import AnyFormAccessMixin
from django.core.paginator import Paginator
from django.http import Http404
from django.utils.http import urlencode
from django.views import View
from django.shortcuts import render
from django.apps import apps

from reports.services.zonal_dq import get_zonal_dq
from reports.services.zonal_dq.main import get_zonal_queryset
from reports.services.zonal_dq.problem_lists import query_label, query_records, serialize_rows
from reports.services.zonal_dq.stats import get_zonal_stats
from utils.roles import get_role_context

PREVIEW_ROWS = 25  # records shown under each query; "See all" opens the query's own pages
PAGE_ROWS = 50


class EdcsTBLISDataQualityView(AnyFormAccessMixin, View):
    access_forms = (access.EDCS_TBLIS,)

    template_name = "reports/data_quality/laboratory/edcs_tblis/data_edcs_tblis_quality_report.html"
    list_template_name = "reports/data_quality/laboratory/edcs_tblis/edcs_tblis_query_list.html"

    def get(self, request, *args, **kwargs):

        # Get model dynamically
        Zonal = apps.get_model("nanopore", "EdcsTblisZonal")

        role_context = get_role_context(request.user)

        # Prepare zone and site mappings for template
        zones = {z.id: z.name for z in role_context.get("zones", [])}
        sites = {s.id: s.name for s in role_context.get("sites", [])}

        # Read filters from URL params
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")

        zone_id = int(zone_id) if zone_id and zone_id.isdigit() else None
        site_id = int(site_id) if site_id and site_id.isdigit() else None
        
        # zone_id_int = int(zone_id) if zone_id and zone_id.isdigit() else None
        # site_id_int = int(site_id) if site_id and site_id.isdigit() else None
        selected_zone_name = zones.get(zone_id, "") if zone_id else "All Zones"
        selected_site_name = sites.get(site_id, "") if site_id else "All Sites"

        # Validate filters against allowed zones/sites
        if zone_id and zone_id not in zones:
            zone_id = None

        if site_id and site_id not in sites:
            site_id = None

        if request.GET.get("query"):
            return self.query_list(request, Zonal, request.GET["query"], zone_id, site_id, zones, sites)

        qs, stats, total_issues, problem_lists = get_zonal_dq(
            request.user,
            Zonal,
            zone_id,
            site_id,
            limit=PREVIEW_ROWS,
        )

        context = {
            "zones": zones,
            "sites": sites,
            "selected_zone": zone_id,
            "selected_site": site_id,
            "selected_zone_name": selected_zone_name,
            "selected_site_name": selected_site_name,
            "total_records": qs.count(),
            "stats": stats,
            **{f"count_{k}": v for k, v in stats.items()},
            "total_issues": total_issues,
            "preview_rows": PREVIEW_ROWS,
            "filter_query": urlencode({k: v for k, v in (("zone", zone_id), ("site", site_id)) if v}),
            **problem_lists,
        }

        return render(request, self.template_name, context)

    def query_list(self, request, Zonal, key, zone_id, site_id, zones, sites):
        """Every record of one query, a page at a time."""
        qs = get_zonal_queryset(request.user, Zonal, zone_id, site_id)
        duplicates = get_zonal_stats(qs)[2] if key == "duplicate_unique_lab_no" else []
        records = query_records(qs, key, duplicates)
        if records is None:
            raise Http404("No such query.")
        page = Paginator(records, PAGE_ROWS).get_page(request.GET.get("page"))
        filters = {k: v for k, v in (("zone", zone_id), ("site", site_id)) if v}
        return render(request, self.list_template_name, {
            "label": query_label(key), "key": key, "page_obj": page, "rows": serialize_rows(page.object_list, key),
            "zones": zones, "sites": sites, "selected_zone": zone_id, "selected_site": site_id,
            "filter_query": urlencode({"query": key, **filters}), "back_query": urlencode(filters),
        })
