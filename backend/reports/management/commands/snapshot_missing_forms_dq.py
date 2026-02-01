from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db.models import Exists, OuterRef

from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot


class Command(BaseCommand):
    help = "Create or update Missing Forms Data Quality snapshot (view-aligned, per site/zone)"

    def handle(self, *args, **options):
        Screening = apps.get_model("nanopore", "Screening")
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

        today = timezone.localdate()
        snapshot, _ = DataQualitySnapshot.objects.get_or_create(snapshot_date=today)

        # Base queryset: all eligible screenings
        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "enrollment",
            "clinic_laboratory",
            "diagnosis",
        ).prefetch_related("regimen_changes").filter(eligible=True)

        # Precompute regimen existence subquery
        regimen_subquery = RegimenChanges.objects.filter(screening=OuterRef("pk"))

        # Aggregate per site + zone
        site_data = {}

        for s in screenings.iterator():
            site = getattr(s, "site", None)
            zone = getattr(getattr(getattr(site, "district", None), "region", None), "zone", None)

            key = (zone.id if zone else None, site.id if site else None)
            if key not in site_data:
                site_data[key] = {
                    "missing_enrollment": 0,
                    "missing_clinic": 0,
                    "missing_diagnosis": 0,
                    "missing_regimen": 0,
                    "missing_zonal": 0,
                }

            # Missing forms
            missing_enrollment = s.enrollment_id is None
            missing_clinic = s.clinic_laboratory_id is None
            missing_diagnosis = s.diagnosis_id is None

            # Missing regimen
            missing_regimen = False
            diagnosis = getattr(s, "diagnosis", None)
            if diagnosis and getattr(diagnosis, "regimen_changed", None):
                if diagnosis.regimen_changed.name == "Yes" and not RegimenChanges.objects.filter(screening=s).exists():
                    missing_regimen = True

            # Missing zonal (only count if clinic lab conditions are met)
            missing_zonal = Screening.objects.filter(
                pk=s.pk,
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
                zonal_laboratory__isnull=True
            ).exists()

            site_data[key]["missing_enrollment"] += int(missing_enrollment)
            site_data[key]["missing_clinic"] += int(missing_clinic)
            site_data[key]["missing_diagnosis"] += int(missing_diagnosis)
            site_data[key]["missing_regimen"] += int(missing_regimen)
            site_data[key]["missing_zonal"] += int(missing_zonal)

        # Save snapshot per site + zone
        for (zone_id, site_id), counts in site_data.items():
            total_issues = sum(counts.values())
            if total_issues == 0:
                continue

            MissingFormsDQSnapshot.objects.update_or_create(
                snapshot=snapshot,
                zone_id=zone_id,
                site_id=site_id,
                defaults={
                    **counts,
                    "total_issues": total_issues,
                }
            )

        self.stdout.write(
            self.style.SUCCESS(f"Missing Forms DQ snapshot created/updated for {today}")
        )
