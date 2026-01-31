# reports/services/zonal_dq_counts.py
from django.apps import apps
from django.db.models import Q, Count, Case, When, IntegerField
from utils.permissions import filter_queryset_by_user_role

def get_zonal_dq_counts(user, zone_id=None, site_id=None):
    """
    Returns a dictionary of zonal laboratory DQ counts for missing/invalid fields,
    including conditional logic for culture, LPA, Nanopore, phenotypic DST, and Xpert XDR.
    """
    ZonalLab = apps.get_model("nanopore", "ZonalLaboratory")
    
    qs = ZonalLab.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district__region__zone"
    )
    qs = filter_queryset_by_user_role(user, qs, site_field="screening__site")

    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(screening__site_id=site_id)

    # Duplicate lab numbers
    duplicate_lab_numbers = (
        qs.exclude(unique_lab_no__isnull=True)
        .exclude(unique_lab_no__exact="")
        .values("unique_lab_no")
        .annotate(cnt=Count("id"))
        .filter(cnt__gt=1)
        .values_list("unique_lab_no", flat=True)
    )

    # ── Aggregated counts ──
    counts = qs.aggregate(
        missing_date_sputum_received=Count(Case(When(date_sputum_received__isnull=True, then=1), output_field=IntegerField())),
        missing_unique_lab_no=Count(Case(When(Q(unique_lab_no__isnull=True) | Q(unique_lab_no__exact=""), then=1), output_field=IntegerField())),
        duplicate_unique_lab_no=Count(Case(When(unique_lab_no__in=duplicate_lab_numbers, then=1), output_field=IntegerField())),
        missing_sample_volume=Count(Case(When(sample_volume__isnull=True, then=1), output_field=IntegerField())),
        missing_appearance=Count(Case(When(appearance__isnull=True, then=1), output_field=IntegerField())),

        # Culture
        missing_culture_method=Count(Case(When(culture_performed=1, culture_method__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
        missing_microscopy_type=Count(Case(When(culture_performed=1, microscopy_type__isnull=True, then=1), output_field=IntegerField())),
        missing_microscopy_date=Count(Case(When(culture_performed=1, microscopy_date__isnull=True, then=1), output_field=IntegerField())),
        missing_microscopy_results=Count(Case(When(culture_performed=1, microscopy_results__isnull=True, then=1), output_field=IntegerField())),

        missing_lj_inoculation_date=Count(Case(When(culture_performed=1, culture_method=1, lj_inoculation_date__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
        missing_lj_results_date=Count(Case(When(culture_performed=1, culture_method=1, lj_results_date__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
        missing_lj_results=Count(Case(When(culture_performed=1, culture_method=1, lj_results__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),

        missing_mgit_inoculation_date=Count(Case(When(culture_performed=1, culture_method=2, mgit_inoculation_date__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
        missing_mgit_results_date=Count(Case(When(culture_performed=1, culture_method=2, mgit_results_date__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
        missing_mgit_results=Count(Case(When(culture_performed=1, culture_method=2, mgit_results__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),

        # Culture isolate & phenotypic DST
        missing_isolate_date=Count(Case(When(Q(culture_isolate__isnull=True) & ~Q(lj_results__in=[1,2,3,4]) & ~Q(mgit_results=1), then=1), output_field=IntegerField())),
        missing_phenotypic_date_performed=Count(Case(When(Q(phenotypic_performed__isnull=True) & Q(culture_isolate=1), then=1), output_field=IntegerField())),
        missing_phenotypic_date_results=Count(Case(When(phenotypic_performed=1, phenotypic_date_results__isnull=True, then=1), output_field=IntegerField())),
        missing_phenotypic_dst_results=Count(Case(When(phenotypic_performed=1, then=Case(
            When(
                Q(rifampicin__isnull=True) |
                Q(isoniazid__isnull=True) |
                Q(levofloxacin__isnull=True) |
                Q(moxifloxacin__isnull=True) |
                Q(bedaquiline__isnull=True) |
                Q(linezolid__isnull=True) |
                Q(clofazimine__isnull=True) |
                Q(cycloserine__isnull=True) |
                Q(terizidone__isnull=True) |
                Q(ethambutol__isnull=True) |
                Q(delamanid__isnull=True) |
                Q(pyrazinamide__isnull=True) |
                Q(imipenem__isnull=True) |
                Q(cilastatin__isnull=True) |
                Q(meropenem__isnull=True) |
                Q(amikacin__isnull=True) |
                Q(streptomycin__isnull=True) |
                Q(ethionamide__isnull=True) |
                Q(prothionamide__isnull=True) |
                Q(para_aminosalicylic_acid__isnull=True),
                then=1
            ), default=None, output_field=IntegerField()
        )), output_field=IntegerField())),

        # Xpert XDR
        missing_xpert_xdr_date_performed=Count(Case(When(xpert_xdr_performed=1, xpert_xdr_date_performed__isnull=True, then=1), output_field=IntegerField())),
        missing_xpert_xdr_results=Count(Case(When(xpert_xdr_performed=1, then=Case(
            When(
                Q(xpert_xdr_isoniazid__isnull=True) |
                Q(xpert_xdr_fluoroquinolones__isnull=True) |
                Q(xpert_xdr_amikacin__isnull=True) |
                Q(xpert_xdr_kanamycin__isnull=True) |
                Q(xpert_xdr_capreomycin__isnull=True) |
                Q(xpert_xdr_ethionamide__isnull=True),
                then=1
            ), default=None, output_field=IntegerField()
        )), output_field=IntegerField())),

        # Nanopore
        missing_nanopore_sequencing_date=Count(Case(When(nanopore_done=1, nanopore_sequencing_date__isnull=True, then=1), output_field=IntegerField())),
        missing_nanopore_results=Count(Case(When(nanopore_done=1, nanopore_results__isnull=True, then=1), output_field=IntegerField())),
        missing_epi_to_me=Count(Case(When(nanopore_done=1, epi_to_me__isnull=True, then=1), output_field=IntegerField())),
        missing_sequencing_delayed=Count(Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed__isnull=True, then=1), output_field=IntegerField())),
        missing_sequencing_delayed_days=Count(Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_days__isnull=True, then=1), output_field=IntegerField())),
        missing_sequencing_delayed_reasons=Count(Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_reasons__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
        missing_sequencing_delayed_others=Count(Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_reasons__value=96, sequencing_delayed_others__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
        missing_epi_to_me_date=Count(Case(When(epi_to_me=1, epi_to_me_date__isnull=True, then=1), output_field=IntegerField())),
        missing_epi_to_me_version=Count(Case(When(epi_to_me=1, epi_to_me_version__isnull=True, then=1), output_field=IntegerField())),
    )

    counts["total_issues"] = sum(counts.values())
    counts["total_records"] = qs.count()

    return counts
