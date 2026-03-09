from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.db.models import Sum
from reports.models import MissingFormsDQSnapshot
from utils.permissions import filter_queryset_by_user_role

def missing_forms_trends(request):
    """
    View to display trends of missing forms.
    Supports filtering by:
    - zone
    - site
    - form (model name)
    - date range (start_date, end_date)
    """

    # --- Get filters safely from GET parameters ---
    zone_id = request.GET.get("zone")
    site_id = request.GET.get("site")
    form_name = request.GET.get("form")
    start_date_raw = request.GET.get("start_date", "")
    end_date_raw = request.GET.get("end_date", "")

    # Parse dates safely
    start_date = parse_date(start_date_raw) if start_date_raw else None
    end_date = parse_date(end_date_raw) if end_date_raw else None

    # --- Base queryset ---
    qs = MissingFormsDQSnapshot.objects.select_related("snapshot")

    # Apply zone, site, form filters
    if zone_id:
        qs = qs.filter(zone_id=zone_id)
    if site_id:
        qs = qs.filter(site_id=site_id)
    if form_name:
        qs = qs.filter(form__iexact=form_name)

    # Apply date range filters
    if start_date:
        qs = qs.filter(snapshot__snapshot_date__gte=start_date)
    if end_date:
        qs = qs.filter(snapshot__snapshot_date__lte=end_date)

    # Aggregate totals by snapshot date
    qs = qs.values("snapshot__snapshot_date").annotate(total=Sum("total_issues")).order_by("snapshot__snapshot_date")

    # Prepare data for chart
    dates = [x["snapshot__snapshot_date"].strftime("%Y-%m-%d") for x in qs]
    totals = [x["total"] for x in qs]

    return render(request, "reports/snapshots/missing_forms_trends.html", {
        "dates": dates,
        "totals": totals,
        "filters": request.GET,  # pass current filters to template
    })