# reports/context_processors.py

from django.apps import apps
from django.db.models import Count, Case, When, IntegerField, Q
from utils.permissions import filter_queryset_by_user_role


def zonal_report_total(request):
    """
    Navbar count for Zonal Laboratory data quality issues.
    """

    if not request.user.is_authenticated:
        return {"zonal_report_total": 0}

    Zonal = apps.get_model("nanopore", "ZonalLaboratory")

    qs = Zonal.objects.all()
    qs = filter_queryset_by_user_role(
        request.user,
        qs,
        site_field="screening__site"
    )

    # =====================================================
    # DUPLICATE UNIQUE LAB NUMBER CHECK
    # =====================================================

    duplicate_lab_numbers = (
        qs.exclude(unique_lab_no__isnull=True)
        .exclude(unique_lab_no__exact="")
        .values("unique_lab_no")
        .annotate(cnt=Count("id"))
        .filter(cnt__gt=1)
        .values_list("unique_lab_no", flat=True)
    )

    # =====================================================
    # DATA QUALITY COUNTS (single DB query with conditions)
    # =====================================================

    stats = qs.aggregate(

        # BASIC REQUIRED FIELDS
        missing_date_sputum_received=Count(
            Case(When(date_sputum_received__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_unique_lab_no=Count(
            Case(
                When(
                    Q(unique_lab_no__isnull=True) |
                    Q(unique_lab_no__exact=""),
                    then=1
                ),
                output_field=IntegerField()
            )
        ),
        duplicate_unique_lab_no=Count(
            Case(
                When(
                    unique_lab_no__in=duplicate_lab_numbers,
                    then=1
                ),
                output_field=IntegerField()
            )
        ),
        missing_sample_volume=Count(
            Case(When(sample_volume__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_appearance=Count(
            Case(When(appearance__isnull=True, then=1), output_field=IntegerField())
        ),

        # CULTURE PERFORMED
        missing_culture_method=Count(
            Case(When(culture_performed=1, culture_method__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_microscopy_type=Count(
            Case(When(culture_performed=1, microscopy_type__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_microscopy_date=Count(
            Case(When(culture_performed=1, microscopy_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_microscopy_results=Count(
            Case(When(culture_performed=1, microscopy_results__isnull=True, then=1), output_field=IntegerField())
        ),

        # LJ CULTURE
        missing_lj_inoculation_date=Count(
            Case(When(culture_performed=1, culture_method=1, lj_inoculation_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lj_results_date=Count(
            Case(When(culture_performed=1, culture_method=1, lj_results_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lj_results=Count(
            Case(When(culture_performed=1, culture_method=1, lj_results__isnull=True, then=1), output_field=IntegerField())
        ),

        # MGIT CULTURE
        missing_mgit_inoculation_date=Count(
            Case(When(culture_performed=1, culture_method=2, mgit_inoculation_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_mgit_results_date=Count(
            Case(When(culture_performed=1, culture_method=2, mgit_results_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_mgit_results=Count(
            Case(When(culture_performed=1, culture_method=2, mgit_results__isnull=True, then=1), output_field=IntegerField())
        ),

        # CULTURE ISOLATE
        missing_isolate_date=Count(
            Case(
                When(
                    Q(culture_isolate__isnull=True) &
                    ~Q(lj_results__in=[1,2,3,4]) &
                    ~Q(mgit_results=1),
                    then=1
                ),
                output_field=IntegerField()
            )
        ),

        # PHENOTYPIC DST
        missing_phenotypic_date_performed=Count(
            Case(
                When(
                    Q(phenotypic_performed__isnull=True) &
                    Q(culture_isolate=1),
                    then=1
                ),
                output_field=IntegerField()
            )
        ),
        missing_phenotypic_date_results=Count(
            Case(When(phenotypic_performed=1, phenotypic_date_results__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_phenotypic_dst_results=Count(
            Case(
                When(
                    phenotypic_performed=1,
                    then=Case(
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
                        ),
                        default=None,
                        output_field=IntegerField()
                    )
                )
            )
        ),

        # XPERT XDR
        missing_xpert_xdr_date_performed=Count(
            Case(When(xpert_xdr_performed=1, xpert_xdr_date_performed__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_xpert_xdr_results=Count(
            Case(
                When(
                    xpert_xdr_performed=1,
                    then=Case(
                        When(
                            Q(xpert_xdr_isoniazid__isnull=True) |
                            Q(xpert_xdr_fluoroquinolones__isnull=True) |
                            Q(xpert_xdr_amikacin__isnull=True) |
                            Q(xpert_xdr_kanamycin__isnull=True) |
                            Q(xpert_xdr_capreomycin__isnull=True) |
                            Q(xpert_xdr_ethionamide__isnull=True),
                            then=1
                        ),
                        default=None,
                        output_field=IntegerField()
                    )
                )
            )
        ),

        # FIRST LINE LPA
        missing_first_line_lpa_date=Count(
            Case(When(first_line_lpa=1, first_line_lpa_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_first_line_drugs=Count(
            Case(When(first_line_lpa=1, first_line_drugs__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lpa1_mtb=Count(
            Case(When(first_line_lpa=1, lpa1_mtb__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lpa1_rif=Count(
            Case(When(first_line_lpa=1, lpa1_rif__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lpa1_inh=Count(
            Case(When(first_line_lpa=1, lpa1_inh__isnull=True, then=1), output_field=IntegerField())
        ),

        # SECOND LINE LPA
        missing_second_line_lpa_date=Count(
            Case(When(second_line_lpa=1, second_line_lpa_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_second_line_drugs=Count(
            Case(When(second_line_lpa=1, second_line_drugs__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lpa2_mtb=Count(
            Case(When(second_line_lpa=1, lpa2_mtb__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lpa2_rfluoroquinolones=Count(
            Case(When(second_line_lpa=1, lpa2_rfluoroquinolones__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lpa2_aminoglycosides=Count(
            Case(When(second_line_lpa=1, lpa2_aminoglycosides__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_lpa2_kanamycin=Count(
            Case(When(second_line_lpa=1, lpa2_kanamycin__isnull=True, then=1), output_field=IntegerField())
        ),

        # NANOPORE
        missing_nanopore_sequencing_date=Count(
            Case(When(nanopore_done=1, nanopore_sequencing_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_nanopore_results=Count(
            Case(When(nanopore_done=1, nanopore_results__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_epi_to_me=Count(
            Case(When(nanopore_done=1, epi_to_me__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_sequencing_delayed=Count(
            Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_sequencing_delayed_days=Count(
            Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_days__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_sequencing_delayed_reasons=Count(
            Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_reasons__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_sequencing_delayed_others=Count(
            Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_reasons=96, sequencing_delayed_others__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_epi_to_me_date=Count(
            Case(When(epi_to_me=1, epi_to_me_date__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_epi_to_me_version=Count(
            Case(When(epi_to_me=1, epi_to_me_version__isnull=True, then=1), output_field=IntegerField())
        ),
        missing_nanopore_drug_results=Count(
            Case(
                When(
                    nanopore_results=1,
                    then=Case(
                        When(
                            Q(nano_amikacin__isnull=True) |
                            Q(nano_bedaquiline__isnull=True) |
                            Q(nano_capreomycin__isnull=True) |
                            Q(nano_clofazimine__isnull=True) |
                            Q(nano_delamanid__isnull=True) |
                            Q(nano_ethambutol__isnull=True) |
                            Q(nano_ethionamide__isnull=True) |
                            Q(nano_isoniazid__isnull=True) |
                            Q(nano_kanamycin__isnull=True) |
                            Q(nano_levofloxacin__isnull=True) |
                            Q(nano_linezolid__isnull=True) |
                            Q(nano_moxifloxacin__isnull=True) |
                            Q(nano_pretomanid__isnull=True) |
                            Q(nano_pyrazinamide__isnull=True) |
                            Q(nano_rifampicin__isnull=True) |
                            Q(nano_streptomycin__isnull=True),
                            then=1
                        ),
                        default=None,
                        output_field=IntegerField()
                    )
                )
            )
        ),
    )

    zonal_report_total = sum(stats.values())

    # =====================================================
    # RETURN (explicit breakdown)
    # =====================================================

    return {
        "zonal_report_total": zonal_report_total,
        **stats
    }
