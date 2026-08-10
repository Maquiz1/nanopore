from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Count, Q, Case, When, IntegerField

from reports.models import DataQualitySnapshot, ZonalLaboratoryDQSnapshot


class Command(BaseCommand):
    help = "Create daily Zonal Laboratory Data Quality snapshot per site and zone"

    def handle(self, *args, **options):
        Zonal = apps.get_model("nanopore", "ZonalLaboratory")

        snapshot, _ = DataQualitySnapshot.objects.get_or_create(
            snapshot_date=timezone.localdate()
        )

        qs = Zonal.objects.select_related(
            "screening__site__district__region__zone"
        )

        groups = qs.values(
            "screening__site__district__region__zone_id",
            "screening__site_id",
        ).distinct()

        for g in groups:
            zone_id = g["screening__site__district__region__zone_id"]
            site_id = g["screening__site_id"]

            group_qs = qs.filter(
                screening__site__district__region__zone_id=zone_id,
                screening__site_id=site_id,
            )

            duplicate_lab_numbers = (
                group_qs.exclude(unique_lab_no__isnull=True)
                        .exclude(unique_lab_no__exact="")
                        .values("unique_lab_no")
                        .annotate(cnt=Count("id"))
                        .filter(cnt__gt=1)
                        .values_list("unique_lab_no", flat=True)
            )

            stats = group_qs.aggregate(
                missing_date_sputum_received=Count(
                    Case(When(date_sputum_received__isnull=True, then=1), output_field=IntegerField())
                ),
                missing_unique_lab_no=Count(
                    Case(When(Q(unique_lab_no__isnull=True) | Q(unique_lab_no__exact=""), then=1),
                         output_field=IntegerField())
                ),
                duplicate_unique_lab_no=Count(
                    Case(When(unique_lab_no__in=duplicate_lab_numbers, then=1),
                         output_field=IntegerField())
                ),
                missing_sample_volume=Count(
                    Case(When(sample_volume__isnull=True, then=1), output_field=IntegerField())
                ),
                missing_appearance=Count(
                    Case(When(appearance__isnull=True, then=1), output_field=IntegerField())
                ),
                
                # Culture
                missing_culture_performed=Count(Case(When(culture_performed__isnull=True, then=1), output_field=IntegerField())),
                missing_culture_method=Count(Case(When(culture_performed=1, culture_method__isnull=True, then=1), output_field=IntegerField())),
                missing_microscopy_type=Count(Case(When(culture_performed=1, microscopy_type__isnull=True, then=1), output_field=IntegerField())),
                missing_microscopy_date=Count(Case(When(culture_performed=1, microscopy_date__isnull=True, then=1), output_field=IntegerField())),
                missing_microscopy_results=Count(Case(When(culture_performed=1, microscopy_results__isnull=True, then=1), output_field=IntegerField())),

                # LJ culture
                missing_lj_inoculation_date=Count(Case(When(culture_performed=1, culture_method=1, lj_inoculation_date__isnull=True, then=1), output_field=IntegerField())),
                missing_lj_results_date=Count(Case(When(culture_performed=1, culture_method=1, lj_results_date__isnull=True, then=1), output_field=IntegerField())),
                missing_lj_results=Count(Case(When(culture_performed=1, culture_method=1, lj_results__isnull=True, then=1), output_field=IntegerField())),

                # MGIT culture
                missing_mgit_inoculation_date=Count(Case(When(culture_performed=1, culture_method=2, mgit_inoculation_date__isnull=True, then=1), output_field=IntegerField())),
                missing_mgit_results_date=Count(Case(When(culture_performed=1, culture_method=2, mgit_results_date__isnull=True, then=1), output_field=IntegerField())),
                missing_mgit_results=Count(Case(When(culture_performed=1, culture_method=2, mgit_results__isnull=True, then=1), output_field=IntegerField())),

                # Culture isolate
                missing_culture_isolate=Count(Case(
                    When(culture_isolate__isnull=True, lj_results__in=[1,2,3,4], then=1),
                    When(culture_isolate__isnull=True, mgit_results=1, then=1),
                    output_field=IntegerField()
                )),
                missing_isolate_date=Count(Case(When(Q(isolate_date__isnull=True) & Q(culture_isolate=1), then=1), output_field=IntegerField())),
                missing_isolate_unique_lab_no=Count(Case(When((Q(isolate_unique_lab_no__isnull=True) | Q(isolate_unique_lab_no="")) & Q(culture_isolate=1), then=1), output_field=IntegerField())),

                # Phenotypic DST
                missing_phenotypic_performed=Count(Case(When(Q(culture_isolate__isnull=False) & Q(culture_isolate=1) & Q(phenotypic_performed__isnull=True), then=1), output_field=IntegerField())),
                missing_phenotypic_date_performed=Count(Case(When(Q(phenotypic_date_performed__isnull=True) & Q(phenotypic_performed=1), then=1), output_field=IntegerField())),
                missing_phenotypic_date_results=Count(Case(When(Q(phenotypic_date_results__isnull=True) & Q(phenotypic_performed=1), then=1), output_field=IntegerField())),
                missing_phenotypic_dst_results=Count(Case(
                    When(phenotypic_performed=1, then=Case(
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
                    ))
                )),

                # Xpert XDR
                missing_xpert_xdr_performed=Count(Case(When(xpert_xdr_performed__isnull=True, then=1), output_field=IntegerField())),
                missing_xpert_xdr_date_performed=Count(Case(When(xpert_xdr_performed=1, xpert_xdr_date_performed__isnull=True, then=1), output_field=IntegerField())),
                missing_xpert_xdr_results=Count(Case(
                    When(xpert_xdr_performed=1, then=Case(
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
                    ))
                )),

                # LPA
                missing_lpa=Count(Case(When(lpa__isnull=True, then=1), output_field=IntegerField())),
                
                # First line LPA
                missing_first_line_lpa_date=Count(Case(When(first_line_lpa=1, first_line_lpa_date__isnull=True, then=1), output_field=IntegerField())),
                missing_first_line_drugs=Count(Case(When(first_line_lpa=1, first_line_drugs__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
                missing_lpa1_mtb=Count(Case(When(first_line_lpa=1, lpa1_mtb__isnull=True, then=1), output_field=IntegerField())),
                missing_lpa1_rif=Count(Case(When(first_line_lpa=1, lpa1_rif__isnull=True, then=1), output_field=IntegerField())),
                missing_lpa1_inh=Count(Case(When(first_line_lpa=1, lpa1_inh__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),

                # Second line LPA
                missing_second_line_lpa_date=Count(Case(When(second_line_lpa=1, second_line_lpa_date__isnull=True, then=1), output_field=IntegerField())),
                missing_second_line_drugs=Count(Case(When(second_line_lpa=1, second_line_drugs__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
                missing_lpa2_mtb=Count(Case(When(second_line_lpa=1, lpa2_mtb__isnull=True, then=1), output_field=IntegerField())),
                missing_lpa2_rfluoroquinolones=Count(Case(When(second_line_lpa=1, lpa2_rfluoroquinolones__isnull=True, then=1), output_field=IntegerField())),
                missing_lpa2_aminoglycosides=Count(Case(When(second_line_lpa=1, lpa2_aminoglycosides__isnull=True, then=1), output_field=IntegerField())),
                missing_lpa2_kanamycin=Count(Case(When(second_line_lpa=1, lpa2_kanamycin__isnull=True, then=1), output_field=IntegerField())),

                # Nanopore
                missing_nanopore_done=Count(Case(When(nanopore_done__isnull=True, then=1), output_field=IntegerField())),
                missing_nanopore_sequencing_date=Count(Case(When(nanopore_done=1, nanopore_sequencing_date__isnull=True, then=1), output_field=IntegerField())),
                missing_nanopore_results=Count(Case(When(nanopore_done=1, nanopore_results__isnull=True, then=1), output_field=IntegerField())),
                
                # EPI to ME
                missing_epi_to_me=Count(Case(When(nanopore_done=1, epi_to_me__isnull=True, then=1), output_field=IntegerField())),
                missing_epi_to_me_date=Count(Case(When(epi_to_me=1, epi_to_me_date__isnull=True, then=1), output_field=IntegerField())),
                missing_epi_to_me_version=Count(Case(When(epi_to_me=1, epi_to_me_version__isnull=True, then=1), output_field=IntegerField())),
                
                # Delays
                missing_sequencing_delayed=Count(Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed__isnull=True, then=1), output_field=IntegerField())),
                missing_sequencing_delayed_days=Count(Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_days__isnull=True, then=1), output_field=IntegerField())),
                missing_sequencing_delayed_reasons=Count(Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_reasons__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
                missing_sequencing_delayed_others=Count(Case(When(nanopore_done=1, nanopore_results=1, sequencing_delayed=1, sequencing_delayed_reasons__value=96, sequencing_delayed_others__isnull=True, then="pk"), output_field=IntegerField(), distinct=True)),
                
                # Nanopore drug results
                missing_nanopore_drug_results=Count(Case(
                    When(nanopore_results=1, then=Case(
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
                    ))
                )),  
            )

            total_issues = sum(v or 0 for v in stats.values())

            ZonalLaboratoryDQSnapshot.objects.update_or_create(
                snapshot=snapshot,
                zone_id=zone_id,
                site_id=site_id,
                defaults={
                    "total_records": group_qs.count(),
                    "total_issues": total_issues,
                    **stats,
                }
            )

        self.stdout.write(
            self.style.SUCCESS("Zonal Laboratory DQ snapshots per site and zone created ✅")
        )
