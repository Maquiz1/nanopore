from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Count, Q

from reports.models import DataQualitySnapshot, EnrollmentDQSnapshot


class Command(BaseCommand):
    help = "Create daily Enrollment Data Quality snapshot (per site, per zone)"

    def handle(self, *args, **options):
        Enrollment = apps.get_model("nanopore", "Enrollment")

        today = timezone.localdate()
        snapshot, _ = DataQualitySnapshot.objects.get_or_create(snapshot_date=today)

        qs = Enrollment.objects.select_related(
            "screening__site__district__region__zone"
        )

        grouped = qs.values(
            "screening__site__district__region__zone_id",
            "screening__site_id",
        ).annotate(

            # =====================================================
            # TOTALS
            # =====================================================
            total_enrollments=Count("id"),

            # =====================================================
            # BASIC REQUIRED FIELDS
            # =====================================================
            missing_hiv_status=Count("id", filter=Q(hiv_status__isnull=True)),
            missing_other_diseases=Count("id", filter=Q(other_diseases__isnull=True)),
            missing_sputum_collected=Count("id", filter=Q(sputum_collected__isnull=True)),

            missing_sputum_date=Count(
                "id",
                filter=Q(sputum_collected=1, sputum_date__isnull=True)
            ),

            missing_sputum_reasons=Count(
                "id",
                filter=Q(sputum_collected=2, sputum_reasons__isnull=True)
            ),

            # =====================================================
            # OTHER DISEASES (M2M)
            # =====================================================
            missing_diseases_medical=Count(
                "id",
                filter=Q(other_diseases=1) & Q(diseases_medical__isnull=True)
            ),

            missing_diseases_specify=Count(
                "id",
                filter=Q(diseases_medical__value=96, diseases_specify__isnull=True)
            ),

            # =====================================================
            # TB TREATMENT
            # =====================================================
            missing_dr_ds=Count(
                "id", filter=Q(tx_previous=1, dr_ds__isnull=True)
            ),

            missing_tb_regimen=Count(
                "id", filter=Q(tx_previous=1, tb_regimen__isnull=True)
            ),

            missing_tb_outcome=Count(
                "id", filter=Q(tx_previous=1, tb_otcome__isnull=True)
            ),

            missing_tb_regimen_specify=Count(
                "id",
                filter=Q(tb_regimen__value=96, tb_regimen_specify__isnull=True)
            ),

            missing_tb_regimen_specify_8=Count(
                "id",
                filter=Q(tb_regimen=8, tb_regimen_specify__isnull=True)
            ),

            missing_tb_category_specify=Count(
                "id",
                filter=Q(tb_category__value=96, tb_category_specify__isnull=True)
            ),

            # =====================================================
            # LTF MONTHS LOGIC
            # =====================================================
            invalid_ltf_months=Count(
                "id",
                filter=Q(tb_category__in=[2, 3]) & ~(
                    Q(ltf_months__isnull=False, ltf_months_unknown=False) |
                    Q(ltf_months__isnull=True, ltf_months_unknown=True)
                )
            ),

            # =====================================================
            # PREVIOUS TB TREATMENT LOGIC
            # =====================================================
            missing_tx_month_without_unknown=Count(
                "id",
                filter=Q(tx_previous=1, tx_month__isnull=True, tx_unknown_month=False)
            ),

            invalid_tx_month_with_unknown=Count(
                "id",
                filter=Q(tx_previous=1, tx_unknown_month=True) & ~(
                    Q(tx_month__isnull=True) | Q(tx_month=99)
                )
            ),

            missing_tx_year_without_unknown=Count(
                "id",
                filter=Q(tx_previous=1, tx_year__isnull=True, tx_unknown_year=False)
            ),

            invalid_tx_year_with_unknown=Count(
                "id",
                filter=Q(tx_previous=1, tx_unknown_year=True) & ~(
                    Q(tx_year__isnull=True) | Q(tx_year=99)
                )
            ),

            invalid_unknown_year_dependencies=Count(
                "id",
                filter=Q(tx_previous=1, tx_unknown_year=True) & ~(
                    Q(tx_unknown_month=True) &
                    (Q(tx_month__isnull=True) | Q(tx_month=99))
                )
            ),

            missing_regimen_months_without_unknown=Count(
                "id",
                filter=Q(tx_previous=1, regimen_months__isnull=True, regimen_months_unknown=False)
            ),

            invalid_regimen_months_with_unknown=Count(
                "id",
                filter=Q(tx_previous=1, regimen_months_unknown=True) & ~Q(regimen_months__isnull=True)
            ),
        )

        rows = []

        for g in grouped:
            total_issues = sum(
                g[k] for k in g if k.startswith(("missing_", "invalid_"))
            )

            rows.append(
                EnrollmentDQSnapshot(
                    snapshot=snapshot,
                    zone_id=g["screening__site__district__region__zone_id"],
                    site_id=g["screening__site_id"],
                    total_enrollments=g["total_enrollments"],
                    total_issues=total_issues,
                    **{k: g[k] for k in g if k.startswith(("missing_", "invalid_"))}
                )
            )

        EnrollmentDQSnapshot.objects.bulk_create(rows, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(f"Enrollment snapshot created for {today}")
        )
