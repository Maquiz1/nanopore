# reports/services/zonal_dq_counts.py
from django.db.models import Q, Count, Case, When, IntegerField

def get_duplicate_lab_numbers(qs):
    return (
        qs.exclude(unique_lab_no__isnull=True)
          .exclude(unique_lab_no__exact="")
          .values("unique_lab_no")
          .annotate(cnt=Count("id"))
          .filter(cnt__gt=1)
          .values_list("unique_lab_no", flat=True)
    )

def get_zonal_dq_counts(qs):
    """
    Return aggregate stats and duplicate lab numbers for a queryset.
    """
    duplicate_lab_numbers = get_duplicate_lab_numbers(qs)

    stats = qs.aggregate(
        # General fields
        missing_date_sputum_received=Count("id", filter=Q(date_sputum_received__isnull=True), distinct=True),
        missing_sample_volume=Count("id", filter=Q(sample_volume__isnull=True), distinct=True),
        missing_appearance=Count("id", filter=Q(appearance__isnull=True), distinct=True),
        missing_unique_lab_no=Count("id", filter=Q(unique_lab_no__isnull=True) | Q(unique_lab_no__exact=""), distinct=True),
        duplicate_unique_lab_no=Count("id", filter=Q(unique_lab_no__in=duplicate_lab_numbers), distinct=True),

        # Culture
        missing_culture_performed=Count("id", filter=Q(culture_performed__isnull=True), distinct=True),
        missing_culture_method=Count("id", filter=Q(culture_performed=1, culture_method__isnull=True), distinct=True),
        missing_microscopy_type=Count("id", filter=Q(culture_performed=1, microscopy_type__isnull=True), distinct=True),
        missing_microscopy_date=Count("id", filter=Q(culture_performed=1, microscopy_date__isnull=True), distinct=True),
        missing_microscopy_results=Count("id", filter=Q(culture_performed=1, microscopy_results__isnull=True), distinct=True),

        # LJ culture
        missing_lj_inoculation_date=Count("id", filter=Q(culture_performed=1, culture_method=1, lj_inoculation_date__isnull=True), distinct=True),
        missing_lj_results_date=Count("id", filter=Q(culture_performed=1, culture_method=1, lj_results_date__isnull=True), distinct=True),
        missing_lj_results=Count("id", filter=Q(culture_performed=1, culture_method=1, lj_results__isnull=True), distinct=True),

        # MGIT culture
        missing_mgit_inoculation_date=Count("id", filter=Q(culture_performed=1, culture_method=2, mgit_inoculation_date__isnull=True), distinct=True),
        missing_mgit_results_date=Count("id", filter=Q(culture_performed=1, culture_method=2, mgit_results_date__isnull=True), distinct=True),
        missing_mgit_results=Count("id", filter=Q(culture_performed=1, culture_method=2, mgit_results__isnull=True), distinct=True),

        # Culture isolate
        missing_culture_isolate = Count(
            "id",
            filter=(
                (Q(lj_results__in=[1,2,3,4]) | Q(mgit_results=1)) & Q(culture_isolate__isnull=True)
            ),
            distinct=True
        ),
        missing_isolate_date=Count("id", filter=Q(culture_isolate=1, isolate_date__isnull=True), distinct=True),
        
        # Phenotypic DST — only if culture_isolate = 1
        missing_phenotypic_performed = Count(
            "id",
            filter=Q(culture_isolate=1) & Q(phenotypic_performed__isnull=True),
            distinct=True
        ),

        # Phenotypic DST date performed — only if phenotypic_performed = 1
        missing_phenotypic_date_performed = Count(
            "id",
            filter=Q(phenotypic_performed=1, phenotypic_date_performed__isnull=True),
            distinct=True
        ),
        # Phenotypic DST date results — only if phenotypic_performed = 1
        missing_phenotypic_date_results = Count(
            "id",
            filter=Q(phenotypic_performed=1, phenotypic_date_results__isnull=True),
            distinct=True
        ),
        # Phenotypic DST results — any missing drug results, only if phenotypic_performed = 1
        missing_phenotypic_dst_results = Count(
            "id",
            filter=Q(phenotypic_performed=1) & (
                Q(rifampicin__isnull=True) | Q(isoniazid__isnull=True) |
                Q(levofloxacin__isnull=True) | Q(moxifloxacin__isnull=True) |
                Q(bedaquiline__isnull=True) | Q(linezolid__isnull=True) |
                Q(clofazimine__isnull=True) | Q(cycloserine__isnull=True) |
                Q(terizidone__isnull=True) | Q(ethambutol__isnull=True) |
                Q(delamanid__isnull=True) | Q(pyrazinamide__isnull=True) |
                Q(imipenem__isnull=True) | Q(cilastatin__isnull=True) |
                Q(meropenem__isnull=True) | Q(amikacin__isnull=True) |
                Q(streptomycin__isnull=True) | Q(ethionamide__isnull=True) |
                Q(prothionamide__isnull=True) | Q(para_aminosalicylic_acid__isnull=True)
            ),
            distinct=True
        ),

        # Xpert/XDR
        missing_xpert_xdr_performed = Count(
            "id",
            filter=Q(xpert_xdr_performed__isnull=True),
            distinct=True
        ),

        missing_xpert_xdr_date_performed = Count(
            "id",
            filter=Q(xpert_xdr_performed=1, xpert_xdr_date_performed__isnull=True),
            distinct=True
        ),

        missing_xpert_xdr_results = Count(
            "id",
            filter=Q(xpert_xdr_performed=1) & (
                Q(xpert_xdr_isoniazid__isnull=True) |
                Q(xpert_xdr_fluoroquinolones__isnull=True) |
                Q(xpert_xdr_amikacin__isnull=True) |
                Q(xpert_xdr_kanamycin__isnull=True) |
                Q(xpert_xdr_capreomycin__isnull=True) |
                Q(xpert_xdr_ethionamide__isnull=True)
            ),
            distinct=True
        ),
        
        # LPA
        missing_lpa = Count(
            "id",
            filter=Q(lpa__isnull=True),
            distinct=True
        ),
        
        # First-line LPA missing details
        missing_first_line_lpa = Count(
            "id",
            filter=Q(lpa=1, first_line_lpa__isnull=True),
            distinct=True
        ),
        missing_first_line_lpa_date = Count(
            "id",
            filter=Q(first_line_lpa=1, first_line_lpa_date__isnull=True),
            distinct=True
        ),
        missing_first_line_drugs = Count(
            "id",
            filter=Q(first_line_lpa=1, first_line_drugs__isnull=True),
            distinct=True
        ),
        missing_lpa1_mtb = Count(
            "id",
            filter=Q(first_line_lpa=1, lpa1_mtb__isnull=True),
            distinct=True
        ),
        missing_lpa1_rif = Count(
            "id",
            filter=Q(first_line_lpa=1, lpa1_rif__isnull=True),
            distinct=True
        ),
        missing_lpa1_inh = Count(
            "id",
            filter=Q(first_line_lpa=1, lpa1_inh__isnull=True),
            distinct=True
        ),
        
        # Second-line LPA missing details
        missing_second_line_lpa = Count(
            "id",
            filter=Q(lpa=1, second_line_lpa__isnull=True),
            distinct=True
        ),
        missing_second_line_lpa_date = Count(
            "id",
            filter=Q(second_line_lpa=1, second_line_lpa_date__isnull=True),
            distinct=True
        ),
        missing_second_line_drugs = Count(
            "id",
            filter=Q(second_line_lpa=1, second_line_drugs__isnull=True),
            distinct=True
        ),
        missing_lpa2_mtb = Count(
            "id",
            filter=Q(second_line_lpa=1, lpa2_mtb__isnull=True),
            distinct=True
        ),
        missing_lpa2_rfluoroquinolones = Count(
            "id",
            filter=Q(second_line_lpa=1, lpa2_rfluoroquinolones__isnull=True),
            distinct=True
        ),
        missing_lpa2_aminoglycosides = Count(
            "id",
            filter=Q(second_line_lpa=1, lpa2_aminoglycosides__isnull=True),
            distinct=True
        ),
        missing_lpa2_kanamycin = Count(
            "id",
            filter=Q(second_line_lpa=1, lpa2_kanamycin__isnull=True),
            distinct=True
        ),

        # Nanopore
        missing_nanopore_done = Count(
            "id",
            filter=Q(nanopore_done__isnull=True),
            distinct=True
        ),

        missing_nanopore_sequencing_date = Count(
            "id",
            filter=Q(nanopore_done=1, nanopore_sequencing_date__isnull=True),
            distinct=True
        ),

        missing_nanopore_results = Count(
            "id",
            filter=Q(nanopore_done=1, nanopore_results__isnull=True),
            distinct=True
        ),

        # EPI TO ME
        missing_epi_to_me = Count(
            "id",
            filter=Q(nanopore_done=1, epi_to_me__isnull=True),
            distinct=True
        ),
        
        missing_epi_to_me_date = Count(
            "id",
            filter=Q(epi_to_me=1, epi_to_me_date__isnull=True),
            distinct=True
        ),

        missing_epi_to_me_version = Count(
            "id",
            filter=Q(epi_to_me=1, epi_to_me_version__isnull=True),
            distinct=True
        ),
        
        missing_sequencing_results = Count(
            "id",
            filter=Q(epi_to_me=1, sequencing_results__isnull=True),
            distinct=True
        ),

        # delayed sequencing
        missing_sequencing_delayed = Count(
            "id",
            filter=Q(nanopore_done=1, sequencing_delayed__isnull=True),
            distinct=True
        ),

        missing_sequencing_delayed_days = Count(
            "id",
            filter=Q(sequencing_delayed=1, sequencing_delayed_days__isnull=True),
            distinct=True
        ),

        missing_sequencing_delayed_reasons = Count(
            "id",
            filter=Q(sequencing_delayed=1, sequencing_delayed_reasons__isnull=True),
            distinct=True
        ),

        # DELAYED SEQUENCING - OTHERS reason
        missing_sequencing_delayed_others = Count(
            "id",
            filter=Q(sequencing_delayed_reasons__value=96, sequencing_delayed_others__isnull=True),
            distinct=True
        ),

        missing_nanopore_drug_results = Count(
            "id",
            filter=Q(nanopore_results=1) & (
                Q(nano_amikacin__isnull=True) | Q(nano_bedaquiline__isnull=True) | Q(nano_capreomycin__isnull=True) |
                Q(nano_clofazimine__isnull=True) | Q(nano_delamanid__isnull=True) | Q(nano_ethambutol__isnull=True) |
                Q(nano_ethionamide__isnull=True) | Q(nano_isoniazid__isnull=True) | Q(nano_kanamycin__isnull=True) |
                Q(nano_levofloxacin__isnull=True) | Q(nano_linezolid__isnull=True) | Q(nano_moxifloxacin__isnull=True) |
                Q(nano_pretomanid__isnull=True) | Q(nano_pyrazinamide__isnull=True) | Q(nano_rifampicin__isnull=True) |
                Q(nano_streptomycin__isnull=True)
            ),
            distinct=True
        ),

    )

    total_issues = sum(stats.values())

    return {
        "stats": stats,
        "total_issues": total_issues,
        "duplicate_lab_numbers": duplicate_lab_numbers
    }
