# reports/views/queries/laboratory/zonal/ctrl_isolates_view.py
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.views import View

from nanopore.models import TblisRawData
from reports.constants.zona_mapping import CTRL_QUERIES
from reports.services.zonal_dq import get_ctrl_isolate_counts, get_ctrl_isolates_queryset, to_complete_q
from reports.services.zonal_dq.filters import get_ctrl_isolate_filters
from reports.services.zonal_dq.serializers import isolate_number
from utils import access
from utils.access_mixins import AnyFormAccessMixin

TO_COMPLETE, COMPLETE, NOT_IN_TBLIS = "to-complete", "complete", "not-in-tblis"


class CtrlIsolatesView(AnyFormAccessMixin, View):
    """Isolates other zones sent to CTRL: the numbers CTRL still has to enter, and the DST still to come from TB-LIS."""
    access_forms = (access.CTRL_ISOLATES,)
    template_name = "reports/data_quality/laboratory/zonal/ctrl_isolates.html"
    paginate_by = 50

    def get(self, request):
        user = request.user
        get = lambda key: request.GET.get(key, "").strip()

        everything = get_ctrl_isolates_queryset(user)
        zones = dict(everything.order_by("screening__site__district__region__zone__name").values_list(
            "screening__site__district__region__zone_id", "screening__site__district__region__zone__name").distinct())
        sites = dict(everything.order_by("screening__site__name").values_list(
            "screening__site_id", "screening__site__name").distinct())
        pick = lambda key, allowed: int(get(key)) if get(key).isdigit() and int(get(key)) in allowed else None
        zone_id, site_id = pick("zone", zones), pick("site", sites)

        qs = get_ctrl_isolates_queryset(user, zone_id, site_id)
        if get("q"):
            qs = qs.filter(Q(screening__pid__icontains=get("q")) | Q(unique_lab_no__icontains=get("q"))
                           | Q(isolate_unique_lab_no__icontains=get("q")))

        filters = get_ctrl_isolate_filters()
        counts = get_ctrl_isolate_counts(user, zone_id, site_id)
        to_complete = qs.filter(to_complete_q())
        complete = qs.filter(culture_isolate=1).exclude(pk__in=to_complete.values("pk"))
        # A number with no isolate row in TB-LIS: not uploaded yet, or mistyped
        not_in_tblis = (qs.exclude(isolate_unique_lab_no__isnull=True).exclude(isolate_unique_lab_no="")
                        .exclude(isolate_unique_lab_no__in=TblisRawData.objects.filter(raw_data__spectype__iexact="isolate").values("labno")))
        tab = get("tab") if get("tab") in (*CTRL_QUERIES, COMPLETE, NOT_IN_TBLIS) else TO_COMPLETE
        records = {COMPLETE: complete, NOT_IN_TBLIS: not_in_tblis, TO_COMPLETE: to_complete}.get(tab)
        if records is None:
            records = qs.filter(filters[tab])

        tabs = [{"key": TO_COMPLETE, "label": "To complete", "count": to_complete.count()},
                {"key": NOT_IN_TBLIS, "label": "Number not in TB-LIS", "count": not_in_tblis.count()},
                {"key": COMPLETE, "label": "Complete", "count": complete.count()}]
        checks = [{"key": key, "label": label, "count": counts[key]} for key, label in CTRL_QUERIES.items() if counts[key]]

        page = Paginator(records, self.paginate_by).get_page(request.GET.get("page"))
        ids = [z.pk for z in page]
        open_queries = {pk: [] for pk in ids}
        for key, query in filters.items():
            for pk in qs.filter(query, pk__in=ids).values_list("pk", flat=True):
                open_queries[pk].append(CTRL_QUERIES[key])
        rows = [{"z": z, "isolate_no": isolate_number(z), "open": open_queries[z.pk]} for z in page]

        params = request.GET.copy()
        params.pop("page", None)
        params.pop("tab", None)
        return render(request, self.template_name, {
            "tabs": tabs, "checks": checks, "tab": tab, "rows": rows, "page_obj": page,
            "total_queries": sum(counts.values()),
            "zones": zones, "sites": sites, "selected_zone": zone_id, "selected_site": site_id, "search": get("q"),
            "filters_active": bool(zone_id or site_id or get("q")),
            "filter_query": params.urlencode(),
            "can_edit": access.can_edit(user, access.CTRL_ISOLATES),
        })
