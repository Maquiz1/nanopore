from django.db.models import Q
from reports.constants.zona_mapping import ZONAL_DQ_FIELD_MAPPING

def get_zonal_dq_filters(model):
    """
    Dynamically generate Q objects for all Zonal DQ fields to serve as 
    the single source of truth for stats.py and problem_lists.py.
    """
    filters = {}

    for key, fields in ZONAL_DQ_FIELD_MAPPING.items():
        if key == "duplicate_unique_lab_no":
            continue

        q = Q()

        # Build missing fields logic
        for f in fields:
            try:
                field_obj = model._meta.get_field(f)
            except Exception:
                continue

            field_type = field_obj.get_internal_type()

            if field_type in ("CharField", "TextField"):
                q |= Q(**{f + "__isnull": True}) | Q(**{f + "__exact": ""})
            else:
                q |= Q(**{f + "__isnull": True})

        # CONDITIONAL GUARDS

        # CULTURE
        if key in [
            "missing_culture_method",
            "missing_microscopy_type",
            "missing_microscopy_date",
            "missing_microscopy_results",
        ]:
            q &= Q(culture_performed=1)

        # LJ
        if key in [
            "missing_lj_inoculation_date",
            "missing_lj_results_date",
            "missing_lj_results",
        ]:
            q &= Q(culture_performed=1, culture_method=1)

        # MGIT
        if key in [
            "missing_mgit_inoculation_date",
            "missing_mgit_results_date",
            "missing_mgit_results",
        ]:
            q &= Q(culture_performed=1, culture_method=2)

        # ISOLATE
        if key == "missing_culture_isolate":
            q &= (Q(lj_results__in=[1, 2, 3, 4]) | Q(mgit_results=1)) & Q(culture_isolate__isnull=True)

        if key == "missing_isolate_date":
            q &= Q(culture_isolate=1)

        # PHENOTYPIC DST
        if key == "missing_phenotypic_performed":
            q &= Q(culture_isolate=1)

        if key in ["missing_phenotypic_date_performed", "missing_phenotypic_date_results", "missing_phenotypic_dst_results"]:
            q &= Q(phenotypic_performed=1)

        # XPERT XDR
        if key in ["missing_xpert_xdr_date_performed", "missing_xpert_xdr_results"]:
            q &= Q(xpert_xdr_performed=1)

        # LPA
        if key == "missing_first_line_lpa":
            q &= Q(lpa=1)

        if key in [
            "missing_first_line_lpa_date",
            "missing_first_line_drugs",
            "missing_lpa1_mtb",
        ]:
            q &= Q(first_line_lpa=1)

        if key in [
            "missing_lpa1_rif",
            "missing_lpa1_inh",
        ]:
            q &= Q(lpa1_mtb=1)

        if key == "missing_second_line_lpa":
            q &= Q(lpa=1)

        if key in [
            "missing_second_line_lpa_date",
            "missing_second_line_drugs",
            "missing_lpa2_mtb",
        ]:
            q &= Q(second_line_lpa=1)

        if key in [
            "missing_lpa2_rfluoroquinolones",
            "missing_lpa2_aminoglycosides",
            "missing_lpa2_kanamycin",
        ]:
            q &= Q(lpa2_mtb=1)

        # NANOPORE
        if key in [
            "missing_nanopore_sequencing_date",
            "missing_epi_to_me",
            "missing_nanopore_results",
            "missing_sequencing_delayed",
        ]:
            q &= Q(nanopore_done=1)

        # EPI TO ME
        if key in [
            "missing_epi_to_me_date",
            "missing_epi_to_me_version",
            "missing_sequencing_results",
        ]:
            q &= Q(epi_to_me=1)

        # DELAYED SEQUENCING
        if key in [
            "missing_sequencing_delayed_days",
            "missing_sequencing_delayed_reasons",
        ]:
            q &= Q(sequencing_delayed=1)

        if key == "missing_sequencing_delayed_others":
            q &= Q(sequencing_delayed_reasons__value=96)

        # Nanopore drug results
        if key == "missing_nanopore_drug_results":
            q &= Q(nanopore_results=1)

        filters[key] = q

    return filters
