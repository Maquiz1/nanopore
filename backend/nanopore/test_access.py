"""
Role + assignment access rules (utils/access.py).

Zone A has two clinics (A1, A2) and a zonal lab (ALAB); zone B has clinic B1.
Every clinic has one screened participant with a zonal lab result.
"""
from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from locations.models import Country, District, Region, Site, SiteLevel, Zone
from nanopore.models import Screening, ZonalLaboratory
from options.models import YesNo
from users.models import Position, Profile
from utils import access
from utils.access import can_edit, can_view, get_accessible_sites, scope_queryset


class AccessTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name in access.ALL_ROLES:
            Group.objects.create(name=name)
        local = SiteLevel.objects.create(name="Local", code="local")
        zonal = SiteLevel.objects.create(name="Zonal", code="zonal")
        country = Country.objects.create(name="Tanzania")
        yes = YesNo.objects.create(name="Yes", value=1)

        def make_zone(name):
            zone = Zone.objects.create(name=name, country=country)
            region = Region.objects.create(name=f"{name} region", country=country, zone=zone)
            district = District.objects.create(name=f"{name} district", region=region)
            return zone, district

        cls.zone_a, district_a = make_zone("Zone A")
        cls.zone_b, district_b = make_zone("Zone B")
        cls.a1 = Site.objects.create(name="A1", district=district_a, pid_prefix="A1-", site_level=local)
        cls.a2 = Site.objects.create(name="A2", district=district_a, pid_prefix="A2-", site_level=local)
        cls.alab = Site.objects.create(name="ALAB", district=district_a, pid_prefix="AL-", site_level=zonal)
        cls.b1 = Site.objects.create(name="B1", district=district_b, pid_prefix="B1-", site_level=local)

        cls.screenings = {}
        cls.zonal_labs = {}
        for site in (cls.a1, cls.a2, cls.b1):
            screening = Screening.objects.create(
                screening_date=date(2025, 3, 1), pid1="001", pid2="001", site=site, eligible=True,
            )
            cls.screenings[site.name] = screening
            cls.zonal_labs[site.name] = ZonalLaboratory.objects.create(
                screening=screening, unique_lab_no=f"LAB-{site.name}", culture_performed=yes,
            )

    @classmethod
    def make_user(cls, username, roles=(), sites=(), zones=(), position=None):
        user = User.objects.create_user(username, password="pw")
        user.groups.set(Group.objects.filter(name__in=roles))
        profile = Profile.objects.create(user=user)
        profile.sites.set(sites)
        profile.zones.set(zones)
        if position:
            profile.position = Position.objects.get_or_create(name=position)[0]
            profile.save()
        return User.objects.get(pk=user.pk)

    def visible_pids(self, user, site_field="site", qs=None):
        qs = Screening.objects.all() if qs is None else qs
        values = scope_queryset(user, qs, site_field)
        field = "pid" if site_field == "site" else "screening__pid"
        return set(values.values_list(field, flat=True))

    def pid(self, site_name):
        return self.screenings[site_name].pid


class ScopeRulesTests(AccessTestBase):
    def test_site_assignment_sees_only_that_site(self):
        nurse = self.make_user("nurse", [access.NURSE], sites=[self.a1])
        self.assertEqual(self.visible_pids(nurse), {self.pid("A1")})

    def test_zone_assignment_sees_every_site_in_zone(self):
        nurse = self.make_user("nurse", [access.NURSE], zones=[self.zone_a])
        self.assertEqual(self.visible_pids(nurse), {self.pid("A1"), self.pid("A2")})

    def test_zone_assignment_overrides_site_assignment(self):
        nurse = self.make_user("nurse", [access.NURSE], sites=[self.b1], zones=[self.zone_a])
        self.assertEqual(self.visible_pids(nurse), {self.pid("A1"), self.pid("A2")})

    def test_lab_tech_on_zonal_lab_site_sees_whole_zone(self):
        lab = self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.alab])
        labs = ZonalLaboratory.objects.all()
        self.assertEqual(
            self.visible_pids(lab, "screening__site", labs), {self.pid("A1"), self.pid("A2")}
        )

    def test_lab_tech_on_local_site_sees_only_that_site(self):
        lab = self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.a1])
        labs = ZonalLaboratory.objects.all()
        self.assertEqual(self.visible_pids(lab, "screening__site", labs), {self.pid("A1")})

    def test_zonal_lab_site_does_not_widen_for_non_lab_roles(self):
        ds = self.make_user("ds", [access.DATA_SPECIALIST], sites=[self.alab])
        self.assertEqual(self.visible_pids(ds), set())

    def test_reviewer_and_admin_are_unscoped(self):
        reviewer = self.make_user("reviewer", [access.REVIEWER])
        admin = self.make_user("admin", [access.ADMIN])
        everyone = set(Screening.objects.values_list("pid", flat=True))
        self.assertEqual(self.visible_pids(reviewer), everyone)
        self.assertEqual(self.visible_pids(admin), everyone)
        self.assertIsNone(get_accessible_sites(reviewer))

    def test_user_without_role_sees_nothing(self):
        nobody = self.make_user("nobody", sites=[self.a1])
        self.assertEqual(self.visible_pids(nobody), set())

    def test_user_without_assignment_sees_nothing(self):
        nurse = self.make_user("nurse", [access.NURSE])
        self.assertEqual(self.visible_pids(nurse), set())


class RoleRulesTests(AccessTestBase):
    def test_nurse_and_clinician_get_clinical_forms_only(self):
        for role in (access.NURSE, access.CLINICIAN):
            user = self.make_user(role.lower(), [role], sites=[self.a1])
            for form in access.CLINICAL_FORMS:
                self.assertTrue(can_edit(user, form), (role, form))
            for form in access.LAB_FORMS:
                self.assertFalse(can_view(user, form), (role, form))

    def test_lab_tech_gets_lab_forms_and_read_only_screening(self):
        lab = self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.alab])
        self.assertTrue(can_edit(lab, access.ZONAL_LAB))
        self.assertTrue(can_edit(lab, access.EDCS_TBLIS))
        self.assertTrue(can_view(lab, access.SCREENING))
        self.assertFalse(can_edit(lab, access.SCREENING))
        self.assertFalse(can_view(lab, access.ENROLLMENT))

    def test_reviewer_is_read_only(self):
        reviewer = self.make_user("reviewer", [access.REVIEWER])
        for form in access.ALL_FORMS:
            self.assertTrue(can_view(reviewer, form))
            self.assertFalse(can_edit(reviewer, form))

    def test_data_specialist_edits_every_form(self):
        ds = self.make_user("ds", [access.DATA_SPECIALIST], sites=[self.a1])
        for form in access.ALL_FORMS:
            self.assertTrue(can_edit(ds, form))

    def test_roles_combine(self):
        user = self.make_user(
            "lab_ds", [access.LABORATORY_TECHNICIAN, access.DATA_SPECIALIST], sites=[self.alab]
        )
        self.assertTrue(can_edit(user, access.ENROLLMENT))
        self.assertTrue(can_edit(user, access.ZONAL_LAB))
        # The lab-site widening applies to the user's whole scope.
        self.assertEqual(self.visible_pids(user), {self.pid("A1"), self.pid("A2")})

    def test_legacy_data_specialist_position_still_counts(self):
        user = self.make_user("legacy", sites=[self.a1], position="Data Specialist")
        self.assertTrue(can_edit(user, access.DIAGNOSIS))
        self.assertEqual(self.visible_pids(user), {self.pid("A1")})


class ViewEnforcementTests(AccessTestBase):
    def login(self, user):
        self.client.force_login(user)

    def test_anonymous_is_sent_to_login(self):
        for name in ("nanopore:screening-list", "nanopore:zonal-laboratory-list", "nanopore:zonal-upload-csv",
                     "nanopore:download-screenings-csv", "reports:summary"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)

    def test_nurse_cannot_open_zonal_lab(self):
        self.login(self.make_user("nurse", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(reverse("nanopore:zonal-laboratory-list")).status_code, 403)
        lab = self.zonal_labs["A1"]
        self.assertEqual(
            self.client.get(reverse("nanopore:zonal-laboratory-detail", args=[lab.pk])).status_code, 403
        )

    def test_lab_tech_list_is_scoped_and_other_forms_forbidden(self):
        self.login(self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        response = self.client.get(reverse("nanopore:zonal-laboratory-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({lab.screening.pid for lab in response.context["object_list"]}, {self.pid("A1")})
        self.assertEqual(self.client.get(reverse("nanopore:enrollment-list")).status_code, 403)
        # Screening is read-only for lab technicians.
        self.assertEqual(self.client.get(reverse("nanopore:screening-create")).status_code, 403)

    def test_record_outside_scope_returns_404(self):
        self.login(self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        other = self.zonal_labs["B1"]
        url = reverse("nanopore:zonal-laboratory-detail", args=[other.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        url = reverse("nanopore:zonal-laboratory-update", args=[other.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_reviewer_can_view_but_not_change(self):
        self.login(self.make_user("reviewer", [access.REVIEWER]))
        screening = self.screenings["B1"]
        self.assertEqual(self.client.get(reverse("nanopore:screening-detail", args=[screening.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("nanopore:screening-delete", args=[screening.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("nanopore:screening-update", args=[screening.pk])).status_code, 403)
        self.assertTrue(Screening.objects.filter(pk=screening.pk).exists())

    def test_nurse_cannot_delete_records(self):
        # Deleting is admin-only (records go to the recycle bin).
        self.login(self.make_user("nurse", [access.NURSE], sites=[self.a1]))
        screening = self.screenings["A1"]
        self.assertEqual(self.client.post(reverse("nanopore:screening-delete", args=[screening.pk])).status_code, 403)
        self.assertTrue(Screening.objects.filter(pk=screening.pk).exists())

    def test_reports_require_reports_feature(self):
        self.login(self.make_user("nurse", [access.NURSE], zones=[self.zone_a]))
        self.assertEqual(self.client.get(reverse("reports:summary")).status_code, 403)

    def test_data_specialist_reports_and_exports_are_scoped(self):
        self.login(self.make_user("ds", [access.DATA_SPECIALIST], sites=[self.a1]))
        response = self.client.get(reverse("reports:summary"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["grand_totals"]["screenings"], 1)

        response = self.client.get(reverse("nanopore:download-screenings-csv"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(self.pid("A1"), body)
        self.assertNotIn(self.pid("B1"), body)

    def test_bulk_uploads_are_superuser_only(self):
        self.login(self.make_user("admin", [access.ADMIN]))
        self.assertEqual(self.client.get(reverse("nanopore:zonal-upload-csv")).status_code, 403)


class MissingFormsTests(AccessTestBase):
    def test_lab_tech_sees_zonal_missing_forms_at_any_site_level(self):
        from reports.services.missing_form_dq_counts import get_missing_forms_counts
        for name, kwargs in [("zonal_site", {"sites": [self.alab]}), ("local_site", {"sites": [self.a1]}),
                             ("zone", {"zones": [self.zone_a]})]:
            lab = self.make_user(name, [access.LABORATORY_TECHNICIAN], **kwargs)
            counts = get_missing_forms_counts(lab)
            # Only zonal gaps count towards a lab technician's total.
            self.assertEqual(counts["total_form_missing"], counts["missing_zonal_count"], name)

            self.client.force_login(lab)
            url = reverse("reports:missing_form_details_queries", args=["zonal"])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, name)
            self.assertNotContains(response, "You do not have permission to view zonal lab records")
            self.assertTrue(response.context["is_zonal_lab"], name)
            url = reverse("reports:missing_form_details_queries", args=["enrollment"])
            self.assertEqual(self.client.get(url).status_code, 403, name)

    def test_lab_tech_form_queries_total_counts_lab_forms_only(self):
        from django.test import RequestFactory
        from reports.context_processors.form_queries.edcs_tblis_laboratory_context_processor import (
            edcs_tblis_report_total,
        )
        from reports.context_processors.form_queries.zonal_laboratory_context import zonal_report_total
        from reports.context_processors.specific_queries_total import specific_queries_total

        lab = self.make_user("lab", [access.LABORATORY_TECHNICIAN], zones=[self.zone_a])
        request = RequestFactory().get("/")
        request.user = lab
        expected = (
            zonal_report_total(request)["context_zonal_report_total"]
            + edcs_tblis_report_total(request)["context_edcs_tblis_report_total"]
        )
        self.assertGreater(zonal_report_total(request)["context_zonal_report_total"], 0)
        self.assertEqual(specific_queries_total(request)["context_specific_queries_total"], expected)


class ExportRolesTests(AccessTestBase):
    def test_who_can_export(self):
        from utils.access import has_feature
        exporters = [access.DATA_SPECIALIST, access.DATA_MANAGER, access.STATISTICIAN, access.ADMIN]
        for role in access.ALL_ROLES:
            user = self.make_user(f"u_{role.lower()}", [role], sites=[self.a1])
            self.assertEqual(has_feature(user, access.EXPORTS), role in exporters, role)

    def test_statistician_is_view_only(self):
        stat = self.make_user("stat", [access.STATISTICIAN], sites=[self.a1])
        for form in access.ALL_FORMS:
            self.assertTrue(can_view(stat, form))
            self.assertFalse(can_edit(stat, form))

    def test_data_manager_edits_like_data_specialist(self):
        dm = self.make_user("dm", [access.DATA_MANAGER], sites=[self.a1])
        for form in access.ALL_FORMS:
            self.assertTrue(can_edit(dm, form))

    def test_export_scope(self):
        from utils.access import export_queryset
        everyone = set(Screening.objects.values_list("pid", flat=True))
        for role in (access.DATA_MANAGER, access.STATISTICIAN):
            user = self.make_user(f"x_{role.lower()}", [role], sites=[self.a1])
            self.assertEqual(set(export_queryset(user, Screening.objects.all()).values_list("pid", flat=True)), everyone, role)
            # their pages still follow their assignment
            self.assertEqual(self.visible_pids(user), {self.pid("A1")})
        ds = self.make_user("x_ds", [access.DATA_SPECIALIST], sites=[self.a1])
        self.assertEqual(set(export_queryset(ds, Screening.objects.all()).values_list("pid", flat=True)), {self.pid("A1")})

    def test_export_page_and_downloads(self):
        self.client.force_login(self.make_user("rev", [access.REVIEWER]))
        page = self.client.get(reverse("reports:codebook"))
        self.assertNotContains(page, "Data export")
        self.assertEqual(self.client.get(reverse("reports:export_data") + "?model=Screening").status_code, 403)

        self.client.force_login(self.make_user("ds2", [access.DATA_SPECIALIST], sites=[self.a1]))
        page = self.client.get(reverse("reports:codebook"))
        self.assertContains(page, "Data export")
        response = self.client.get(reverse("reports:export_data") + "?model=Screening&mode=full")
        body = b"".join(response.streaming_content).decode()
        self.assertIn(self.pid("A1"), body)
        self.assertNotIn(self.pid("B1"), body)
