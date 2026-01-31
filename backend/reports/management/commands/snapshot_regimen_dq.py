# reports/management/commands/create_regimen_dq_snapshot.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Count, Q, F

from reports.models import DataQualitySnapshot, RegimenDQSnapshot


class Command(BaseCommand):
    help = "Create daily Regimen Data Quality snapshot"

    def handle(self, *args, **options):
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

        snapshot, _ = DataQualitySnapshot.objects.get_or_create(
            snapshot_date=timezone.localdate()
        )

        qs = RegimenChanges.objects.select_related(
            "screening",
            "screening__site",
            "screening__site__district",
            "screening__site__district__region",
            "screening__site__district__region__zone",
            "changes",
            "reason",
        )

        grouped = qs.values(
            "screening__site__district__region__zone_id",
            "screening__site_id",
        ).annotate(
            total_regimens=Count("id"),

            missing_date=Count("id", filter=Q(date__isnull=True)),
            missing_drug=Count("id", filter=Q(drug__isnull=True) | Q(drug__exact="")),
            missing_changes=Count("id", filter=Q(changes__isnull=True)),
            missing_reason=Count("id", filter=Q(reason__isnull=True)),
            missing_specify_when_other=Count(
                "id",
                filter=(
                    Q(reason__value=96) | Q(reason__name__iexact="96") | Q(reason__name__iexact="other")
                ) & (Q(specify__isnull=True) | Q(specify__exact=""))
            ),
        )

        rows = []
        for g in grouped:
            total_issues = sum([
                g["missing_date"],
                g["missing_drug"],
                g["missing_changes"],
                g["missing_reason"],
                g["missing_specify_when_other"],
            ])

            rows.append(
                RegimenDQSnapshot(
                    snapshot=snapshot,
                    zone_id=g["screening__site__district__region__zone_id"],
                    site_id=g["screening__site_id"],
                    total_regimens=g["total_regimens"],
                    total_issues=total_issues,

                    missing_date=g["missing_date"],
                    missing_drug=g["missing_drug"],
                    missing_changes=g["missing_changes"],
                    missing_reason=g["missing_reason"],
                    missing_specify_when_other=g["missing_specify_when_other"],
                )
            )

        RegimenDQSnapshot.objects.bulk_create(
            rows,
            ignore_conflicts=True
        )

        self.stdout.write(
            self.style.SUCCESS("Regimen data quality snapshot created")
        )
