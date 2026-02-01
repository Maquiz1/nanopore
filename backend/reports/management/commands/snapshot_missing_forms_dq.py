from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps

from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot

class Command(BaseCommand):
    help = "Create Missing Forms Data Quality snapshot"

    def handle(self, *args, **options):
        Screening = apps.get_model("nanopore", "Screening")
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

        snapshot, _ = DataQualitySnapshot.objects.get_or_create(snapshot_date=timezone.localdate())

        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "diagnosis",
            "clinic_laboratory",
            "zonal_laboratory",
            "enrollment"
        ).prefetch_related("regimen_changes").filter(eligible=True)

        rows = []

        for s in screenings:
            has_regimen_subquery = RegimenChanges.objects.filter(screening=s)

            missing_enrollment = s.enrollment is None
            missing_clinic = s.clinic_laboratory is None
            missing_diagnosis = s.diagnosis is None

            # ✅ Safe check for regimen_changed
            missing_regimen = False
            if not has_regimen_subquery.exists() and s.diagnosis:
                regimen_changed = getattr(s.diagnosis, "regimen_changed", None)
                if regimen_changed and getattr(regimen_changed, "name", None) == "Yes":
                    missing_regimen = True

            missing_zonal = (
                s.zonal_laboratory is None
                and s.clinic_laboratory
                and getattr(s.clinic_laboratory, "xpert_mtb_rif_conducted", 0) == 1
                and getattr(s.clinic_laboratory, "xpert_mtb", 0) in [2, 3, 4, 5, 6]
            )

            total_issues = sum([missing_enrollment, missing_clinic, missing_diagnosis, missing_regimen, missing_zonal])

            if total_issues > 0:
                zone = getattr(getattr(getattr(s.site, "district", None), "region", None), "zone", None)
                rows.append(
                    MissingFormsDQSnapshot(
                        snapshot=snapshot,
                        zone_id=zone.id if zone else None,
                        site_id=s.site.id if s.site else None,
                        screening_id=s.id,
                        missing_enrollment=missing_enrollment,
                        missing_clinic=missing_clinic,
                        missing_diagnosis=missing_diagnosis,
                        missing_regimen=missing_regimen,
                        missing_zonal=missing_zonal,
                        total_issues=total_issues
                    )
                )

        if rows:
            MissingFormsDQSnapshot.objects.bulk_create(rows, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("Missing Forms Data Quality snapshot created"))
