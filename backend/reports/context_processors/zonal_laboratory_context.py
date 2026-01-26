from django.apps import apps
from utils.permissions import filter_queryset_by_user_role

def zonal_report_total(request):
    """
    Returns total Zonal Laboratory issues count for navbar:
    - Counts ZonalLaboratory records with missing critical fields
    """
    zonal_total = 0

    # if not request.user.is_authenticated:
    #     return {"zonal_report_total": zonal_total}

    # ZonalLaboratory = apps.get_model('nanopore', 'ZonalLaboratory')
    # zonals = ZonalLaboratory.objects.all()
    # zonals = filter_queryset_by_user_role(request.user, zonals, site_field="screening__site")

    # # --- Required fields to check (core process completeness) ---
    # required_fields = [
    #     # Specimen receipt
    #     "date_sputum_received",
    #     "appearance",
    #     "sample_volume",
    #     "unique_lab_no",

    #     # Culture
    #     "culture_performed",
    #     "microscopy_type",
    #     "microscopy_date",
    #     "microscopy_results",

    #     # LJ results
    #     "lj_inoculation_date",
    #     "lj_results_date",
    #     "lj_results",

    #     # MGIT results
    #     "mgit_inoculation_date",
    #     "mgit_results_date",
    #     "mgit_results",

    #     # Culture isolate
    #     "culture_isolate",
    #     "isolate_date",

    #     # Nanopore sequencing (end stage)
    #     "nanopore_done",
    #     "nanopore_sequencing_date",
    #     "sequencing_results",
    #     "nanopore_results",
    # ]

    # for z in zonals:
    #     for field in required_fields:
    #         value = getattr(z, field)
    #         if value in [None, "", False]:
    #             zonal_total += 1
    #             break  # Count each record only once

    return {"zonal_report_total": zonal_total}
