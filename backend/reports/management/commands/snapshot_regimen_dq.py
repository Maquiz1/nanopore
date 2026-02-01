from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Count, Q

from reports.models import DataQualitySnapshot, RegimenDQSnapshot


class Command(BaseCommand):
    help = "Create daily Regimen Data Quality snapshot (per site, per zone)"

    def handle(self, *args, **options):
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

        snapshot, _ = DataQualitySnapshot.objects.get_or_create(
            snapshot_date=timezone.localdate()
        )

        qs = RegimenChanges.objects.select_related(
            "screening__site__district__region__zone",
            "changes",
            "reason",
        )

        # Reason = 96 (Other)
        reason_is_96_q = (
            Q(reason__value=96)
            | Q(reason__name__iexact="96")
            | Q(reason__name__iexact="other")
        )

        grouped = qs.values(
            "screening__site__district__region__zone_id",
            "screening__site_id",
        ).annotate(
            total_regimens=Count("id"),

            missing_date=Count("id", filter=Q(date__isnull=True)),
            missing_drug=Count("id", filter=Q(drug__isnull=True)),
            missing_changes=Count("id", filter=Q(changes__isnull=True)),
            missing_reason=Count("id", filter=Q(reason__isnull=True)),

            missing_specify_when_other=Count(
                "id",
                filter=reason_is_96_q & Q(specify__isnull=True)
            ),
        )

        for g in grouped:
            total_issues = sum([
                g["missing_date"],
                g["missing_drug"],
                g["missing_changes"],
                g["missing_reason"],
                g["missing_specify_when_other"],
            ])

            RegimenDQSnapshot.objects.update_or_create(
                snapshot=snapshot,
                zone_id=g["screening__site__district__region__zone_id"],
                site_id=g["screening__site_id"],
                defaults={
                    "total_regimens": g["total_regimens"],
                    "total_issues": total_issues,

                    "missing_date": g["missing_date"],
                    "missing_drug": g["missing_drug"],
                    "missing_changes": g["missing_changes"],
                    "missing_reason": g["missing_reason"],
                    "missing_specify_when_other": g["missing_specify_when_other"],
                },
            )

        self.stdout.write(
            self.style.SUCCESS("Regimen Data Quality snapshot created/updated successfully")
        )
