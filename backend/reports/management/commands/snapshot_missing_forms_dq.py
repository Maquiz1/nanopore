# reports/management/commands/snapshot_missing_forms_dq.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps

from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot

class Command(BaseCommand):
    help = "Create or update Missing Forms Data Quality snapshot (view-aligned, per site/zone)"

    def handle(self, *args, **options):
        Screening = apps.get_model("nanopore", "Screening")
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

        today = timezone.localdate()
        snapshot, _ = DataQualitySnapshot.objects.get_or_create(snapshot_date=today)

        # Fetch screenings
        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "enrollment",
        ).prefetch_related(
            "regimen_changes"
        ).all()

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

            # --- Missing enrollment ---
            try:
                enrollment = s.enrollment
            except Screening.enrollment.RelatedObjectDoesNotExist:
                enrollment = None
            missing_enrollment = enrollment is None

            # --- Missing clinic laboratory ---
            try:
                clinic_lab = s.clinic_laboratory
            except Screening.clinic_laboratory.RelatedObjectDoesNotExist:
                clinic_lab = None
            missing_clinic = clinic_lab is None

            # --- Missing diagnosis ---
            try:
                diagnosis = s.diagnosis
            except Screening.diagnosis.RelatedObjectDoesNotExist:
                diagnosis = None
            missing_diagnosis = diagnosis is None

            # --- Missing regimen changes ---
            missing_regimen = False
            if diagnosis and diagnosis.regimen_changed:
                if diagnosis.regimen_changed.name.strip().lower() == "yes":
                    if not RegimenChanges.objects.filter(screening=s).exists():
                        missing_regimen = True

            # --- Missing zonal lab (only if clinic lab exists and conditions met) ---
            missing_zonal = False
            if clinic_lab:
                if getattr(clinic_lab.xpert_mtb_rif_conducted, "name", "").strip().lower() == "yes":
                    if getattr(clinic_lab.xpert_mtb, "id", None) in [2, 3, 4, 5, 6]:
                        try:
                            zonal_lab = s.zonal_laboratory
                            if zonal_lab is None:
                                missing_zonal = True
                        except Screening.zonal_laboratory.RelatedObjectDoesNotExist:
                            missing_zonal = True

            # --- Aggregate counts ---
            site_data[key]["missing_enrollment"] += int(missing_enrollment)
            site_data[key]["missing_clinic"] += int(missing_clinic)
            site_data[key]["missing_diagnosis"] += int(missing_diagnosis)
            site_data[key]["missing_regimen"] += int(missing_regimen)
            site_data[key]["missing_zonal"] += int(missing_zonal)

        # --- Save snapshots ---
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
