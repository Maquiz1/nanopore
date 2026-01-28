from django.apps import apps
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def zonal_report_total(request):
    """
    Navbar count for Zonal Laboratory issues.

    Counts incomplete existing ZonalLaboratory forms by checking each required field
    individually using the same style as screening_report_total.
    Does NOT include "missing zonal forms" — that is handled in forms_report_total.
    """
    zonal_total = 0

    if not request.user.is_authenticated:
        return {"zonal_report_total": zonal_total}

    # ── Models ────────────────────────────────────────────────────────
    ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")

    # ── Fetch zonal forms visible to the current user ─────────────────
    qs = ZonalLaboratory.objects.all()

    qs = filter_queryset_by_user_role(
        request.user,
        qs,
        site_field="screening__site"
    )

    # ── Missing / Null fields (each checked separately) ───────────────
    missing_date_sputum_received = qs.filter(date_sputum_received__isnull=True).count()
    missing_appearance           = qs.filter(appearance__isnull=True).count()
    missing_sample_volume        = qs.filter(sample_volume__isnull=True).count()
    missing_unique_lab_no        = qs.filter(unique_lab_no__isnull=True).count()

    # ── Grand total ───────────────────────────────────────────────────
    total_issues = (
        missing_date_sputum_received +
        missing_appearance +
        missing_sample_volume +
        missing_unique_lab_no
    )

    zonal_total += total_issues

    return {
        "zonal_report_total": zonal_total
    }