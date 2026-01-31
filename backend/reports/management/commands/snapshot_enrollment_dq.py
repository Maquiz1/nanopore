from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Count, Q, F

from reports.models import DataQualitySnapshot, EnrollmentDQSnapshot


class Command(BaseCommand):
    help = "Create daily Enrollment Data Quality snapshot (per site, per zone)"

    def handle(self, *args, **options):
        Enrollment = apps.get_model("nanopore", "Enrollment")

        today = timezone.localdate()

        snapshot, _ = DataQualitySnapshot.objects.get_or_create(
            snapshot_date=today
        )

        qs = Enrollment.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district",
            "screening__site__district__region",
            "screening__site__district__region__zone",
        )

        grouped = qs.values(
            "screening__site__district__region__zone_id",
            "screening__site_id",
        ).annotate(

            # ----------------------------
            # Totals
            # ----------------------------
            total_enrollments=Count("id"),

            # ----------------------------
            # Core missing fields
            # ----------------------------
            missing_hiv_status=Count(
                "id", filter=Q(hiv_status__isnull=True)
            ),

            missing_other_diseases=Count(
                "id", filter=Q(other_diseases__isnull=True)
            ),

            # ----------------------------
            # Sputum logic
            # ----------------------------
            missing_sputum_collected=Count(
                "id", filter=Q(sputum_collected__isnull=True)
            ),

            missing_sputum_date=Count(
                "id",
                filter=Q(sputum_collected=1, sputum_date__isnull=True)
            ),

            missing_sputum_reasons=Count(
                "id",
                filter=Q(sputum_collected=0, sputum_not_collected_reason__isnull=True)
            ),

            # ----------------------------
            # Diseases / medical conditions
            # ----------------------------
            missing_diseases_medical=Count(
                "id",
                filter=Q(diseases_medical_conditions__isnull=True)
            ),

            missing_diseases_specify=Count(
                "id",
                filter=Q(
                    diseases_medical_conditions__value=96,
                    diseases_specify__isnull=True
                )
            ),

            # ----------------------------
            # Drug resistance / regimen
            # ----------------------------
            missing_dr_ds=Count(
                "id",
                filter=Q(dr_ds__isnull=True)
            ),

            missing_tb_regimen=Count(
                "id",
                filter=Q(tb_regimen__isnull=True)
            ),

            missing_tb_outcome=Count(
                "id",
                filter=Q(tb_outcome__isnull=True)
            ),

            missing_tb_regimen_specify=Count(
                "id",
                filter=Q(tb_regimen__value=96, tb_regimen_specify__isnull=True)
            ),

            missing_tb_regimen_specify_8=Count(
                "id",
                filter=Q(tb_regimen__value=8, tb_regimen_specify__isnull=True)
            ),

            missing_tb_category_specify=Count(
                "id",
                filter=Q(tb_category__value=96, tb_category_specify__isnull=True)
            ),

            # ----------------------------
            # LTFU months
            # ----------------------------
            invalid_ltf_months=Count(
                "id",
                filter=Q(ltf_months__lt=0) | Q(ltf_months__gt=60)
            ),

            # ----------------------------
            # Treatment start month/year logic
            # ----------------------------
            missing_tx_month_without_unknown=Count(
                "id",
                filter=Q(
                    tx_month__isnull=True,
                    tx_month_unknown=0
                )
            ),

            invalid_tx_month_with_unknown=Count(
                "id",
                filter=Q(
                    tx_month__isnull=False,
                    tx_month_unknown=1
                )
            ),

            missing_tx_year_without_unknown=Count(
                "id",
                filter=Q(
                    tx_year__isnull=True,
                    tx_year_unknown=0
                )
            ),

            invalid_tx_year_with_unknown=Count(
                "id",
                filter=Q(
                    tx_year__isnull=False,
                    tx_year_unknown=1
                )
            ),

            invalid_unknown_year_dependencies=Count(
                "id",
                filter=Q(
                    tx_year_unknown=1,
                    tx_month_unknown=0
                )
            ),

            # ----------------------------
            # Regimen months
            # ----------------------------
            missing_regimen_months_without_unknown=Count(
                "id",
                filter=Q(
                    regimen_months__isnull=True,
                    regimen_months_unknown=0
                )
            ),

            invalid_regimen_months_with_unknown=Count(
                "id",
                filter=Q(
                    regimen_months__isnull=False,
                    regimen_months_unknown=1
                )
            ),
        )

        rows = []

        for g in grouped:
            total_issues = sum([
                g["missing_hiv_status"],
                g["missing_other_diseases"],
                g["missing_sputum_collected"],
                g["missing_sputum_date"],
                g["missing_sputum_reasons"],
                g["missing_diseases_medical"],
                g["missing_diseases_specify"],
                g["missing_dr_ds"],
                g["missing_tb_regimen"],
                g["missing_tb_outcome"],
                g["missing_tb_regimen_specify"],
                g["missing_tb_regimen_specify_8"],
                g["missing_tb_category_specify"],
                g["invalid_ltf_months"],
                g["missing_tx_month_without_unknown"],
                g["invalid_tx_month_with_unknown"],
                g["missing_tx_year_without_unknown"],
                g["invalid_tx_year_with_unknown"],
                g["invalid_unknown_year_dependencies"],
                g["missing_regimen_months_without_unknown"],
                g["invalid_regimen_months_with_unknown"],
            ])

            rows.append(
                EnrollmentDQSnapshot(
                    snapshot=snapshot,
                    zone_id=g["screening__site__district__region__zone_id"],
                    site_id=g["screening__site_id"],
                    total_enrollments=g["total_enrollments"],
                    total_issues=total_issues,

                    missing_hiv_status=g["missing_hiv_status"],
                    missing_other_diseases=g["missing_other_diseases"],
                    missing_sputum_collected=g["missing_sputum_collected"],
                    missing_sputum_date=g["missing_sputum_date"],
                    missing_sputum_reasons=g["missing_sputum_reasons"],
                    missing_diseases_medical=g["missing_diseases_medical"],
                    missing_diseases_specify=g["missing_diseases_specify"],
                    missing_dr_ds=g["missing_dr_ds"],
                    missing_tb_regimen=g["missing_tb_regimen"],
                    missing_tb_outcome=g["missing_tb_outcome"],
                    missing_tb_regimen_specify=g["missing_tb_regimen_specify"],
                    missing_tb_regimen_specify_8=g["missing_tb_regimen_specify_8"],
                    missing_tb_category_specify=g["missing_tb_category_specify"],
                    invalid_ltf_months=g["invalid_ltf_months"],
                    missing_tx_month_without_unknown=g["missing_tx_month_without_unknown"],
                    invalid_tx_month_with_unknown=g["invalid_tx_month_with_unknown"],
                    missing_tx_year_without_unknown=g["missing_tx_year_without_unknown"],
                    invalid_tx_year_with_unknown=g["invalid_tx_year_with_unknown"],
                    invalid_unknown_year_dependencies=g["invalid_unknown_year_dependencies"],
                    missing_regimen_months_without_unknown=g["missing_regimen_months_without_unknown"],
                    invalid_regimen_months_with_unknown=g["invalid_regimen_months_with_unknown"],
                )
            )

        EnrollmentDQSnapshot.objects.bulk_create(
            rows,
            ignore_conflicts=True
        )

        self.stdout.write(
            self.style.SUCCESS(f"Enrollment snapshot created for {today}")
        )

