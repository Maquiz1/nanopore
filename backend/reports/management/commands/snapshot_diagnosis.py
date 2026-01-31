from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Count, Q, F

from reports.models import DataQualitySnapshot, DiagnosisDQSnapshot


class Command(BaseCommand):
    help = "Create daily Diagnosis Data Quality snapshot"

    def handle(self, *args, **options):
        Diagnosis = apps.get_model("nanopore", "Diagnosis")

        snapshot, _ = DataQualitySnapshot.objects.get_or_create(
            snapshot_date=timezone.localdate()
        )

        qs = Diagnosis.objects.select_related(
            "screening__site__district__region__zone"
        )

        grouped = qs.values(
            "screening__site__district__region__zone_id",
            "screening__site_id",
        ).annotate(
            total_diagnoses=Count("id"),

            missing_tb_diagnosis=Count("id", filter=Q(tb_diagnosis__isnull=True)),
            missing_tb_diagnosis_date=Count("id", filter=Q(tb_diagnosis=1, tb_diagnosis_date__isnull=True)),
            missing_tb_diagnosis_made=Count("id", filter=Q(tb_diagnosis=1, tb_diagnosis_made__isnull=True)),
            missing_tb_treatment=Count("id", filter=Q(tb_diagnosis=1, tb_treatment__isnull=True)),

            missing_diagnosis_made_other=Count(
                "id",
                filter=Q(tb_diagnosis=1, tb_diagnosis_made__value=96, diagnosis_made_other__isnull=True)
            ),

            missing_tb_diagnosed_clinically=Count(
                "id",
                filter=Q(tb_diagnosis=1, tb_diagnosis_made=1) &
                       Q(tb_diagnosed_clinically__isnull=True)
            ),

            missing_tb_clinically_other=Count(
                "id",
                filter=Q(tb_diagnosed_clinically__value=96, tb_clinically_other__isnull=True)
            ),

            missing_bacteriological_diagnosis=Count(
                "id",
                filter=Q(tb_diagnosis=1, tb_diagnosis_made=2, bacteriological_diagnosis__isnull=True)
            ),

            missing_clinician_received_date=Count(
                "id",
                filter=Q(tb_diagnosis=1, tb_diagnosis_made=2, clinician_received_date__isnull=True)
            ),

            missing_tb_other_diagnosis=Count(
                "id",
                filter=Q(tb_diagnosis=2, tb_other_diagnosis__isnull=True)
            ),

            missing_tb_diagnosis_made2=Count(
                "id",
                filter=Q(tb_diagnosis=2, tb_diagnosis_made2__isnull=True)
            ),

            missing_tb_other_specify=Count(
                "id",
                filter=Q(tb_other_diagnosis__value=96, tb_other_specify__isnull=True)
            ),

            missing_tb_treatment_date=Count(
                "id",
                filter=Q(tb_treatment=1, tb_treatment_date__isnull=True)
            ),

            missing_tb_register_number=Count(
                "id",
                filter=Q(tb_treatment=1, tb_register_number__isnull=True)
            ),

            missing_tb_regimen=Count(
                "id",
                filter=Q(tb_treatment=1, tb_regimen__isnull=True)
            ),

            missing_regimen_changed=Count(
                "id",
                filter=Q(tb_treatment=1, regimen_changed__isnull=True)
            ),

            missing_tb_facility=Count(
                "id",
                filter=Q(tb_treatment=2, tb_facility__isnull=True)
            ),

            missing_tb_reason=Count(
                "id",
                filter=Q(tb_treatment=96, tb_reason__isnull=True)
            ),
        )

        rows = []
        for g in grouped:
            total_issues = sum(v for k, v in g.items() if k.startswith("missing_"))

            rows.append(
                DiagnosisDQSnapshot(
                    snapshot=snapshot,
                    zone_id=g["screening__site__district__region__zone_id"],
                    site_id=g["screening__site_id"],
                    total_diagnoses=g["total_diagnoses"],
                    total_issues=total_issues,
                    **{k: g[k] for k in g if k.startswith("missing_")}
                )
            )

        DiagnosisDQSnapshot.objects.bulk_create(rows, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("Diagnosis snapshot created"))
