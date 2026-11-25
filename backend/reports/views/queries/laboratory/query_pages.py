"""
Long query lists in pages, for the Zonal Lab and EDCS/TBLIS query pages: each query lists its
first PREVIEW_ROWS records, and ?query=<key> shows all its records PAGE_ROWS to a page.
"""
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import urlencode

from reports.services.zonal_dq.main import get_zonal_queryset
from reports.services.zonal_dq.problem_lists import query_label, query_records, serialize_rows
from reports.services.zonal_dq.stats import get_zonal_stats

PREVIEW_ROWS = 25
PAGE_ROWS = 50


class QueryPagesMixin:
    form_label = ""           # "Zonal Lab", "EDCS / TB-LIS"
    report_url_name = ""      # the query page itself
    show_isolate = False      # the Isolate Lab No. column
    list_template_name = "reports/data_quality/laboratory/query_list.html"

    row_link = None  # row -> URL of the form a PID opens; None: the query's own fix form (problem_lists.fix_url_name)

    def preview_context(self, zone_id, site_id):
        return {"preview_rows": PREVIEW_ROWS,
                "filter_query": urlencode({k: v for k, v in (("zone", zone_id), ("site", site_id)) if v})}

    def query_list(self, request, model, key, zone_id, site_id, zones, sites):
        """Every record of one query, a page at a time."""
        qs = get_zonal_queryset(request.user, model, zone_id, site_id)
        duplicates = get_zonal_stats(qs)[2] if key == "duplicate_unique_lab_no" else []
        records = query_records(qs, key, duplicates)
        if records is None:
            raise Http404("No such query.")
        page = Paginator(records, PAGE_ROWS).get_page(request.GET.get("page"))
        filters = {k: v for k, v in (("zone", zone_id), ("site", site_id)) if v}
        return render(request, self.list_template_name, {
            "label": query_label(key), "key": key, "page_obj": page,
            "rows": serialize_rows(page.object_list, key, None if self.row_link is None else (lambda item: self.row_link(item, key))),
            "form_label": self.form_label, "report_url": reverse(self.report_url_name), "show_isolate": self.show_isolate,
            "zones": zones, "sites": sites, "selected_zone": zone_id, "selected_site": site_id,
            "filter_query": urlencode({"query": key, **filters}), "back_query": urlencode(filters),
        })
