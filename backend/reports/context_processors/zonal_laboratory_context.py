from django.apps import apps
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def zonal_report_total(request):
    """
    Navbar count for Zonal Laboratory issues.

    Includes:
    1) Incomplete zonal laboratory forms (missing required fields)
    2) Eligible screenings sent to zonal lab but with NO zonal form created
    """

    zonal_total = 0

    if not request.user.is_authenticated:
        return {"zonal_report_total": zonal_total}

    # --------------------------------------------------
    # Models
    # --------------------------------------------------
    ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")
    Screening = apps.get_model("nanopore", "Screening")

    # --------------------------------------------------
    # Role context
    # --------------------------------------------------
    role_context = get_role_context(request.user)

    is_zonal_lab = role_context.get("is_zonal_lab", False)
    is_admin = role_context.get("is_admin", False)
    is_reviewer = role_context.get("is_reviewer", False)

    # --------------------------------------------------
    # Required zonal completeness fields
    # --------------------------------------------------
    required_fields = [
        "date_sputum_received",
        "appearance",
        "sample_volume",
        "unique_lab_no",
    ]

    # --------------------------------------------------
    # 1️⃣ Incomplete zonal laboratory forms
    # --------------------------------------------------
    zonals = ZonalLaboratory.objects.all()

    zonals = filter_queryset_by_user_role(
        request.user,
        zonals,
        site_field="screening__site"
    )

    incomplete_zonal_forms = 0

    for z in zonals:
        for field in required_fields:
            value = getattr(z, field, None)
            if value in (None, "", False):
                incomplete_zonal_forms += 1
                break  # count once per form

    zonal_total += incomplete_zonal_forms

    # --------------------------------------------------
    return {
        "zonal_report_total": zonal_total
    }
