from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, ContentType
from locations.models import SiteType, SiteLevel
from nanopore.models import Screening, Enrollment, ClinicLaboratory, Diagnosis, ZonalLaboratory, RegimenChanges, EdcsTblisZonal


class Command(BaseCommand):
    help = "Seed default site types, site levels, and user groups with permissions"

    def handle(self, *args, **kwargs):
        # 1. Seed SiteType
        site_types = [
            ("Clinic", "clinic"),
            ("Laboratory", "laboratory"),
        ]
        for name, code in site_types:
            obj, created = SiteType.objects.get_or_create(name=name, code=code)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created SiteType: {name}"))

        # 2. Seed SiteLevel
        site_levels = [
            ("Local", "local"),
            ("Zonal", "zonal"),
            ("National", "national"),
        ]
        for name, code in site_levels:
            obj, created = SiteLevel.objects.get_or_create(name=name, code=code)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created SiteLevel: {name}"))

        # 3. Create Groups
        groups = ["NURSE", "CLINICIAN", "LABORATORY_TECHNICIAN", "DATA_SPECIALIST", "DATA_MANAGER", "STATISTICIAN", "ADMIN", "REVIEWER"]
        for g in groups:
            group, created = Group.objects.get_or_create(name=g)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Group: {g}"))

        # Helper to assign full model permissions
        def assign_full_perms(group_name, models):
            group = Group.objects.get(name=group_name)
            for model in models:
                content_type = ContentType.objects.get_for_model(model)
                perms = Permission.objects.filter(content_type=content_type)
                group.permissions.add(*perms)

        # Helper to assign view-only permissions
        def assign_view_only_perms(group_name, models):
            group = Group.objects.get(name=group_name)
            for model in models:
                content_type = ContentType.objects.get_for_model(model)
                view_perms = Permission.objects.filter(content_type=content_type, codename__startswith='view_')
                group.permissions.add(*view_perms)

        # 4. Assign permissions (mirrors utils/access.py, which is what the views enforce)
        # NURSE & CLINICIAN -> clinical forms (full perms)
        nurse_models = [Screening, Enrollment, ClinicLaboratory, Diagnosis, RegimenChanges]
        assign_full_perms("NURSE", nurse_models)
        assign_full_perms("CLINICIAN", nurse_models)

        # LAB_TECHNICIAN -> Zonal Laboratory + EDCS/TBLIS (full perms), Screening (view only)
        lab_models = [ZonalLaboratory, EdcsTblisZonal]
        assign_full_perms("LABORATORY_TECHNICIAN", lab_models)
        assign_view_only_perms("LABORATORY_TECHNICIAN", [Screening])

        all_models = [Screening, Enrollment, ClinicLaboratory, ZonalLaboratory, EdcsTblisZonal, Diagnosis, RegimenChanges]

        # DATA_SPECIALIST / DATA_MANAGER -> All forms (full perms), limited to their assignment
        assign_full_perms("DATA_SPECIALIST", all_models)
        assign_full_perms("DATA_MANAGER", all_models)

        # STATISTICIAN -> All models (view only); exports cover all sites
        assign_view_only_perms("STATISTICIAN", all_models)

        # ADMIN -> All models (full perms)
        assign_full_perms("ADMIN", all_models)

        # REVIEWER -> All models (view only)
        assign_view_only_perms("REVIEWER", all_models)

        self.stdout.write(self.style.SUCCESS("✅ Roles, site types, and site levels seeded successfully."))
