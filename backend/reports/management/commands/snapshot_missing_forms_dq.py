# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.apps import apps

# from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot

# class Command(BaseCommand):
#     help = "Create Missing Forms Data Quality snapshot"

#     def handle(self, *args, **options):
#         Screening = apps.get_model("nanopore", "Screening")
#         RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

#         snapshot, _ = DataQualitySnapshot.objects.get_or_create(snapshot_date=timezone.localdate())

#         screenings = Screening.objects.select_related(
#             "site",
#             "site__district__region__zone",
#             "diagnosis",
#             "clinic_laboratory",
#             "zonal_laboratory",
#             "enrollment"
#         ).prefetch_related("regimen_changes").filter(eligible=True)

#         rows = []

#         for s in screenings:
#             has_regimen_subquery = RegimenChanges.objects.filter(screening=s)

#             missing_enrollment = s.enrollment is None
#             missing_clinic = s.clinic_laboratory is None
#             missing_diagnosis = s.diagnosis is None

#             # ✅ Safe check for regimen_changed
#             missing_regimen = False
#             if not has_regimen_subquery.exists() and s.diagnosis:
#                 regimen_changed = getattr(s.diagnosis, "regimen_changed", None)
#                 if regimen_changed and getattr(regimen_changed, "name", None) == "Yes":
#                     missing_regimen = True

#             missing_zonal = (
#                 s.zonal_laboratory is None
#                 and s.clinic_laboratory
#                 and getattr(s.clinic_laboratory, "xpert_mtb_rif_conducted", 0) == 1
#                 and getattr(s.clinic_laboratory, "xpert_mtb", 0) in [2, 3, 4, 5, 6]
#             )

#             total_issues = sum([missing_enrollment, missing_clinic, missing_diagnosis, missing_regimen, missing_zonal])

#             if total_issues > 0:
#                 zone = getattr(getattr(getattr(s.site, "district", None), "region", None), "zone", None)
#                 rows.append(
#                     MissingFormsDQSnapshot(
#                         snapshot=snapshot,
#                         zone_id=zone.id if zone else None,
#                         site_id=s.site.id if s.site else None,
#                         screening_id=s.id,
#                         missing_enrollment=missing_enrollment,
#                         missing_clinic=missing_clinic,
#                         missing_diagnosis=missing_diagnosis,
#                         missing_regimen=missing_regimen,
#                         missing_zonal=missing_zonal,
#                         total_issues=total_issues
#                     )
#                 )

#         if rows:
#             MissingFormsDQSnapshot.objects.bulk_create(rows, ignore_conflicts=True)

#         self.stdout.write(self.style.SUCCESS("Missing Forms Data Quality snapshot created"))



# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.apps import apps

# from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot


# class Command(BaseCommand):
#     help = "Create or update Missing Forms Data Quality snapshot"

#     def handle(self, *args, **options):
#         Screening = apps.get_model("nanopore", "Screening")
#         RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

#         today = timezone.localdate()
#         snapshot, _ = DataQualitySnapshot.objects.get_or_create(
#             snapshot_date=today
#         )

#         screenings = (
#             Screening.objects
#             .select_related(
#                 "site",
#                 "site__district__region__zone",
#                 "diagnosis",
#                 "clinic_laboratory",
#                 "zonal_laboratory",
#                 "enrollment"
#             )
#             .prefetch_related("regimen_changes")
#             .filter(eligible=True)
#         )

#         for s in screenings:
#             has_regimen = RegimenChanges.objects.filter(screening=s).exists()

#             missing_enrollment = s.enrollment is None
#             missing_clinic = s.clinic_laboratory is None
#             missing_diagnosis = s.diagnosis is None

#             # ── Regimen logic (safe) ───────────────────────────
#             missing_regimen = False
#             if not has_regimen and s.diagnosis:
#                 regimen_changed = getattr(s.diagnosis, "regimen_changed", None)
#                 if regimen_changed and getattr(regimen_changed, "name", None) == "Yes":
#                     missing_regimen = True

#             # ── Zonal logic ───────────────────────────────────
#             missing_zonal = (
#                 s.zonal_laboratory is None
#                 and s.clinic_laboratory
#                 and getattr(s.clinic_laboratory, "xpert_mtb_rif_conducted", 0) == 1
#                 and getattr(s.clinic_laboratory, "xpert_mtb", 0) in [2, 3, 4, 5, 6]
#             )

#             total_issues = sum([
#                 missing_enrollment,
#                 missing_clinic,
#                 missing_diagnosis,
#                 missing_regimen,
#                 missing_zonal,
#             ])

#             # Skip clean records (keeps table small and meaningful)
#             if total_issues == 0:
#                 continue

#             zone = (
#                 getattr(
#                     getattr(
#                         getattr(s.site, "district", None),
#                         "region", None
#                     ),
#                     "zone", None
#                 )
#             )

#             MissingFormsDQSnapshot.objects.update_or_create(
#                 snapshot=snapshot,
#                 screening_id=s.id,
#                 defaults={
#                     "zone_id": zone.id if zone else None,
#                     "site_id": s.site.id if s.site else None,
#                     "missing_enrollment": missing_enrollment,
#                     "missing_clinic": missing_clinic,
#                     "missing_diagnosis": missing_diagnosis,
#                     "missing_regimen": missing_regimen,
#                     "missing_zonal": missing_zonal,
#                     "total_issues": total_issues,
#                 }
#             )

#         self.stdout.write(
#             self.style.SUCCESS(
#                 f"Missing Forms DQ snapshot created/updated for {today}"
#             )
#         )



# # Match The Missing Form Dashboard 

# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.apps import apps
# from django.db.models import Exists, OuterRef

# from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot


# class Command(BaseCommand):
#     help = "Create or update Missing Forms Data Quality snapshot (aligned with dashboard)"

#     def handle(self, *args, **options):
#         Screening      = apps.get_model("nanopore", "Screening")
#         RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

#         today = timezone.localdate()
#         snapshot, _ = DataQualitySnapshot.objects.get_or_create(
#             snapshot_date=today
#         )

#         screenings = Screening.objects.select_related(
#             "site",
#             "site__district__region__zone",
#             "enrollment",
#             "clinic_laboratory",
#             "diagnosis",
#         ).filter(eligible=True)

#         regimen_subquery = RegimenChanges.objects.filter(
#             screening=OuterRef("pk")
#         )

#         for s in screenings:
#             # ── Missing Enrollment ───────────────────────────
#             missing_enrollment = s.enrollment_id is None

#             # ── Missing Clinic ───────────────────────────────
#             missing_clinic = s.clinic_laboratory_id is None

#             # ── Missing Diagnosis ────────────────────────────
#             missing_diagnosis = s.diagnosis_id is None

#             # ── Missing Regimen (EXACT view logic) ───────────
#             missing_regimen = (
#                 s.diagnosis_id is not None
#                 and s.diagnosis.regimen_changed
#                 and s.diagnosis.regimen_changed.name == "Yes"
#                 and not RegimenChanges.objects.filter(screening=s).exists()
#             )

#             # ── Missing Zonal (EXACT view logic) ─────────────
#             missing_zonal = Screening.objects.filter(
#                 pk=s.pk,
#                 clinic_laboratory__xpert_mtb_rif_conducted=1,
#                 clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
#                 zonal_laboratory__isnull=True
#             ).exists()

#             total_issues = sum([
#                 missing_enrollment,
#                 missing_clinic,
#                 missing_diagnosis,
#                 missing_regimen,
#                 missing_zonal,
#             ])

#             if total_issues == 0:
#                 continue

#             zone = (
#                 s.site.district.region.zone
#                 if s.site and s.site.district and s.site.district.region
#                 else None
#             )

#             MissingFormsDQSnapshot.objects.update_or_create(
#                 snapshot=snapshot,
#                 screening_id=s.id,
#                 defaults={
#                     "zone_id": zone.id if zone else None,
#                     "site_id": s.site_id,
#                     "missing_enrollment": missing_enrollment,
#                     "missing_clinic": missing_clinic,
#                     "missing_diagnosis": missing_diagnosis,
#                     "missing_regimen": missing_regimen,
#                     "missing_zonal": missing_zonal,
#                     "total_issues": total_issues,
#                 }
#             )

#         self.stdout.write(
#             self.style.SUCCESS(
#                 f"Missing Forms DQ snapshot created/updated for {today}"
#             )
#         )


# # Match The Missing Form Details View
# # reports/management/commands/snapshot_missing_forms_dq.py
# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.apps import apps
# from django.core.exceptions import ObjectDoesNotExist

# from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot


# class Command(BaseCommand):
#     help = "Create or update Missing Forms Data Quality snapshot (view-aligned)"

#     def handle(self, *args, **options):
#         Screening = apps.get_model("nanopore", "Screening")
#         RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

#         today = timezone.localdate()
#         snapshot, _ = DataQualitySnapshot.objects.get_or_create(snapshot_date=today)

#         screenings = Screening.objects.select_related(
#             "site",
#             "site__district__region__zone",
#             "enrollment",
#             "clinic_laboratory",
#             "diagnosis",
#         ).filter(eligible=True)

#         def related_exists(obj, attr_name):
#             """
#             Safely checks whether a reverse one-to-one/relation exists without
#             letting RelatedObjectDoesNotExist bubble up.
#             Returns the related object if present, otherwise None.
#             """
#             try:
#                 return getattr(obj, attr_name)
#             except ObjectDoesNotExist:
#                 return None

#         for s in screenings.iterator():
#             # -------------------------
#             # Missing enrollment/clinic/diagnosis (view-aligned)
#             # -------------------------
#             missing_enrollment = related_exists(s, "enrollment") is None
#             missing_clinic = related_exists(s, "clinic_laboratory") is None
#             missing_diagnosis = related_exists(s, "diagnosis") is None

#             # -------------------------
#             # Missing regimen (view logic)
#             # - only relevant if diagnosis exists AND diagnosis.regimen_changed indicates "Yes"
#             # - and there are no RegimenChanges rows for this screening
#             # -------------------------
#             missing_regimen = False
#             diagnosis = related_exists(s, "diagnosis")
#             if diagnosis is not None:
#                 regimen_changed = getattr(diagnosis, "regimen_changed", None)
#                 if regimen_changed and getattr(regimen_changed, "name", None) == "Yes":
#                     # Use an existence query (efficient)
#                     if not RegimenChanges.objects.filter(screening_id=s.pk).exists():
#                         missing_regimen = True

#             # -------------------------
#             # Missing zonal — follow your view's DB-query logic (safe)
#             # -------------------------
#             missing_zonal = Screening.objects.filter(
#                 pk=s.pk,
#                 clinic_laboratory__xpert_mtb_rif_conducted=1,
#                 clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
#                 zonal_laboratory__isnull=True,
#             ).exists()

#             total_issues = sum([
#                 missing_enrollment,
#                 missing_clinic,
#                 missing_diagnosis,
#                 missing_regimen,
#                 missing_zonal,
#             ])

#             if total_issues == 0:
#                 # nothing to store for this screening
#                 continue

#             # Resolve zone safely
#             zone = None
#             site = getattr(s, "site", None)
#             if site is not None:
#                 district = getattr(site, "district", None)
#                 region = getattr(district, "region", None) if district is not None else None
#                 zone = getattr(region, "zone", None) if region is not None else None

#             # Create or update the snapshot row for this screening
#             MissingFormsDQSnapshot.objects.update_or_create(
#                 snapshot=snapshot,
#                 screening_id=s.pk,
#                 defaults={
#                     "zone_id": zone.id if zone else None,
#                     "site_id": site.id if site else None,
#                     "missing_enrollment": int(missing_enrollment),
#                     "missing_clinic": int(missing_clinic),
#                     "missing_diagnosis": int(missing_diagnosis),
#                     "missing_regimen": int(missing_regimen),
#                     "missing_zonal": int(missing_zonal),
#                     "total_issues": int(total_issues),
#                 },
#             )

#         self.stdout.write(
#             self.style.SUCCESS(f"Missing Forms DQ snapshot created/updated for {today}")
#         )


from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Exists, OuterRef

from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot


class Command(BaseCommand):
    help = "Create or update Missing Forms Data Quality snapshot (per site, per zone, view-aligned)"

    def handle(self, *args, **options):
        Screening = apps.get_model("nanopore", "Screening")
        RegimenChanges = apps.get_model("nanopore", "RegimenChanges")

        today = timezone.localdate()
        snapshot, _ = DataQualitySnapshot.objects.get_or_create(snapshot_date=today)

        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "enrollment",
            "clinic_laboratory",
            "diagnosis",
        ).filter(eligible=True)

        # Group per site + zone
        site_data = {}

        for s in screenings.iterator():
            zone = None
            site = getattr(s, "site", None)
            if site:
                district = getattr(site, "district", None)
                region = getattr(district, "region", None) if district else None
                zone = getattr(region, "zone", None) if region else None

            key = (zone.id if zone else None, site.id if site else None)
            if key not in site_data:
                site_data[key] = {
                    "missing_enrollment": 0,
                    "missing_clinic": 0,
                    "missing_diagnosis": 0,
                    "missing_regimen": 0,
                    "missing_zonal": 0,
                }

            # Check missing forms per screening
            missing_enrollment = s.enrollment_id is None
            missing_clinic = s.clinic_laboratory_id is None
            missing_diagnosis = s.diagnosis_id is None

            missing_regimen = False
            diagnosis = getattr(s, "diagnosis", None)
            if diagnosis and getattr(diagnosis, "regimen_changed", None):
                if diagnosis.regimen_changed.name == "Yes":
                    if not RegimenChanges.objects.filter(screening=s).exists():
                        missing_regimen = True

            missing_zonal = Screening.objects.filter(
                pk=s.pk,
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2,3,4,5,6],
                zonal_laboratory__isnull=True,
            ).exists()

            site_data[key]["missing_enrollment"] += int(missing_enrollment)
            site_data[key]["missing_clinic"] += int(missing_clinic)
            site_data[key]["missing_diagnosis"] += int(missing_diagnosis)
            site_data[key]["missing_regimen"] += int(missing_regimen)
            site_data[key]["missing_zonal"] += int(missing_zonal)

        # Create or update snapshot rows per site+zone
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
                },
            )

        self.stdout.write(
            self.style.SUCCESS(f"Missing Forms DQ snapshot created/updated for {today}")
        )
