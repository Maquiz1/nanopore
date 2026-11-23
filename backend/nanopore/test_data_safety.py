"""Export files stay with their owner, results with their patient, and writing within the assignment."""
import csv
import os
import tempfile
from datetime import date
from unittest import mock

from django.core.cache import cache
from django.urls import reverse

from locations.models import District, Region, Site, SiteLevel, Zone
from nanopore.models import Diagnosis, EdcsTblisZonal, RegimenChanges, Screening, TblisRawData, TblisUploadBatch, ZonalLaboratory
from nanopore.test_access import AccessTestBase
from options.models import PhenotypicDSTResults, YesNo, YesNoNA
from reports.tasks_export_models import export_all_models_combined_task
from utils import access


class DataSafetyBase(AccessTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.yes = YesNo.objects.get(pk=1)
        cls.no = YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})[0]
        country = cls.zone_a.country
        dar = Zone.objects.create(name="Dar es salaam", country=country)
        region = Region.objects.create(name="Dar region", country=country, zone=dar)
        district = District.objects.create(name="Temeke", region=region)
        cls.ctrl = Site.objects.create(name="CTRL Laboratory", district=district, pid_prefix="CT-",
                                       site_level=SiteLevel.objects.get(code="zonal"))
        cls.dar_site = Site.objects.create(name="Temeke Hospital", district=district, pid_prefix="DF_TZ_SS2_18_",
                                           site_level=SiteLevel.objects.get(code="local"))
        cls.dar = Screening.objects.create(screening_date=date(2025, 3, 1), pid1="002", pid2="002", site=cls.dar_site, eligible=True)

    def setUp(self):
        cache.clear()


class ExportFileTests(DataSafetyBase):
    def test_edcs_route_serves_only_the_users_own_export(self):
        user = self.make_user("lab_file", [access.DATA_SPECIALIST], zones=[self.zone_a])
        self.client.force_login(user)
        own = f"export_merged_20261122_abcd1234_u{user.pk}.xlsx"
        others = ("export_merged_20261122_abcd1234.xlsx", f"export_merged_20261122_abcd1234_u9{user.pk}.xlsx",
                  "all_models_combined_zonal_2026-11-22_u999.csv", f"all_models_combined_zonal_2026-11-22_u{user.pk}.csv")
        with tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            for name in (own, *others):
                with open(os.path.join(folder, name), "w") as handle:
                    handle.write("synthetic")
            response = self.client.get(reverse("nanopore:edcs-tblis-export-serve", args=[own]))
            self.assertEqual(response.status_code, 200)
            b"".join(response.streaming_content)  # the test client closes it; close() would also drop the database connection
            for name in others:
                self.assertEqual(self.client.get(reverse("nanopore:edcs-tblis-export-serve", args=[name])).status_code, 404, name)

    def test_export_is_named_for_the_user_who_asked(self):
        user = self.make_user("lab_name", [access.DATA_SPECIALIST], zones=[self.zone_a])
        self.client.force_login(user)
        with mock.patch("nanopore.views.laboratory.edcs_tblis.edcs_tblis_csv_export_views.export_edcs_tblis_csv.delay") as delay:
            delay.return_value.id = "task"
            name = self.client.post(reverse("nanopore:edcs-tblis-export-trigger"), {"card_type": "../../x"}).json()["filename"]
        self.assertTrue(name.endswith(f"_u{user.pk}.xlsx"))
        self.assertNotIn("/", name)

    def test_models_route_does_not_serve_raw_tblis_excel_exports(self):
        self.client.force_login(self.make_user("stat_file", [access.STATISTICIAN]))
        with tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            name = "export_ctrl_20261122_abcd1234_u999.xlsx"
            with open(os.path.join(folder, name), "w") as handle:
                handle.write("synthetic")
            self.assertEqual(self.client.get(reverse("reports:serve_model_data", args=[name])).status_code, 404)


class IsolateNumberTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        self.lab = self.zonal_labs["B1"]
        self.resistant = PhenotypicDSTResults.objects.create(pk=1, name="Resistant", value=1)
        self.susceptible = PhenotypicDSTResults.objects.create(pk=2, name="Susceptible", value=2)
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(
            culture_isolate=YesNoNA.objects.create(pk=1, name="Yes", value=1), isolate_unique_lab_no="WRONG",
            phenotypic_performed=self.yes, phenotypic_date_performed=date(2025, 5, 1), first_line_dst_performed=self.yes,
            first_line_dst_results_date=date(2025, 5, 1), rifampicin=self.resistant, isoniazid=self.resistant,
            ethionamide=self.susceptible, remarks="Site remark",
        )
        EdcsTblisZonal.objects.create(screening=self.lab.screening, unique_lab_no="LAB-B1", rifampicin=self.resistant)
        self.client.force_login(self.make_user("ctrl_num", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))

    def change_to(self, number):
        # What the form posts: the current question 11 answers, the number and, for a correction, a reason
        lab = ZonalLaboratory.objects.get(pk=self.lab.pk)
        response = self.client.post(reverse("nanopore:ctrl-isolate-update", args=[self.lab.pk]), {"culture_isolate": lab.culture_isolate_id or "", "isolate_date": lab.isolate_date or "", "isolate_unique_lab_no": number,
                 "reason_for_change": "Corrected from the CTRL register"})
        self.assertEqual(response.status_code, 302)
        return ZonalLaboratory.objects.get(pk=self.lab.pk), EdcsTblisZonal.objects.get(screening=self.lab.screening)

    def test_changed_number_drops_the_old_numbers_dst_at_once(self):
        for record in self.change_to("RIGHT"):
            for name in ("phenotypic_performed", "phenotypic_date_performed", "first_line_dst_performed",
                         "first_line_dst_results_date", "rifampicin", "isoniazid"):
                self.assertIsNone(getattr(record, name), name)
            self.assertEqual((record.isolate_unique_lab_no, record.remarks), ("RIGHT", "Site remark"))
            self.assertEqual(record.ethionamide, self.susceptible)  # the site's own answer

    def test_site_field_is_cleared_when_the_old_number_filled_it(self):
        TblisRawData.objects.create(labno="WRONG", raw_data={"spectype": "Isolate", "mgitdst2_ethionamide": "Sensitive"})
        self.assertIsNone(self.change_to("RIGHT")[0].ethionamide)

    def test_row_without_dst_does_not_bring_the_old_yes_back(self):
        TblisRawData.objects.create(labno="RIGHT", raw_data={"spectype": "Isolate", "labno": "RIGHT"})
        for record in self.change_to("RIGHT"):
            self.assertIsNone(record.phenotypic_performed)  # 12a: empty without a DST date
            self.assertIsNone(record.rifampicin)

    def test_new_numbers_results_replace_the_old(self):
        TblisRawData.objects.create(labno="RIGHT", raw_data={
            "spectype": "Isolate", "labno": "RIGHT", "ljdst1_date": "2025-06-01", "ljdst1_rifampicin": "Sensitive",
        })
        for record in self.change_to("RIGHT"):
            self.assertEqual((record.phenotypic_performed, record.rifampicin), (self.yes, self.susceptible))
            self.assertIsNone(record.isoniazid)

    def test_same_number_keeps_its_dst(self):
        self.assertEqual(self.change_to("WRONG")[0].rifampicin, self.resistant)

    def test_first_number_keeps_what_the_site_entered(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(isolate_unique_lab_no=None)
        self.assertEqual(self.change_to("FIRST")[0].rifampicin, self.resistant)

    def test_cleared_number_drops_its_dst(self):
        ZonalLaboratory.objects.filter(pk=self.lab.pk).update(culture_isolate=None)
        for record in self.change_to(""):
            self.assertIsNone(record.isolate_unique_lab_no)
            self.assertIsNone(record.rifampicin)


class CombinedExportTests(DataSafetyBase):
    def export(self):
        with tempfile.TemporaryDirectory() as folder, self.settings(PRIVATE_EXPORTS_DIR=folder):
            user = self.make_user("stat_comb", [access.STATISTICIAN])
            export_all_models_combined_task.apply(kwargs={"mode": "edcs", "filename": "c.csv", "user_id": user.pk}).get()
            with open(os.path.join(folder, "c.csv"), encoding="utf-8") as handle:
                return {row["pid"]: row for row in csv.DictReader(handle)}

    def test_participant_without_lab_record_is_kept(self):
        self.assertIn(self.dar.pid, self.export())

    def test_unmerged_dar_lab_is_blank_but_participant_is_kept(self):
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001")
        row = self.export()[self.dar.pid]
        self.assertEqual(row["unique_lab_no"], "")
        self.assertEqual(row["screening_date"], "2025-03-01")

    def test_merged_dar_lab_is_shown(self):
        EdcsTblisZonal.objects.create(screening=self.dar, unique_lab_no="30001")
        TblisRawData.objects.create(labno="30001", upload_batch=TblisUploadBatch.objects.create(source_file_name="t.csv"),
                                    is_merged=True, raw_data={"spectype": "Sputum", "peripheralres_genexpert": "MTB Detected"})
        self.assertEqual(self.export()[self.dar.pid]["unique_lab_no"], "30001")


class WriteScopeTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        self.mixed = self.make_user("rev_ds", [access.REVIEWER, access.DATA_SPECIALIST], zones=[self.zone_a])
        self.client.force_login(self.mixed)
        self.lab_b = self.zonal_labs["B1"]
        self.b = self.screenings["B1"]

    def test_reviewer_still_reads_every_zone(self):
        for url in (reverse("nanopore:screening-update", args=[self.b.pk]),
                    reverse("nanopore:zonal-laboratory-update", args=[self.lab_b.pk])):
            page = self.client.get(url)
            self.assertEqual(page.status_code, 200, url)
            self.assertTrue(all(f.disabled for f in page.context["form"].fields.values()), url)
            self.assertNotContains(page, "💾 Save Zonal Laboratory")
            self.assertNotContains(page, "Save screening</button>")

    def test_saving_outside_the_assignment_is_refused(self):
        for url in (reverse("nanopore:screening-update", args=[self.b.pk]),
                    reverse("nanopore:zonal-laboratory-update", args=[self.lab_b.pk])):
            self.assertEqual(self.client.post(url, {}).status_code, 404, url)

    def test_creating_outside_the_assignment_is_refused(self):
        for name in ("enrollment-create", "clinic-laboratory-create", "diagnosis-create", "zonal-laboratory-create"):
            url = reverse(f"nanopore:{name}") + f"?screening={self.b.pk}"
            self.assertEqual(self.client.get(url).status_code, 404, name)
            self.assertEqual(self.client.post(url, {}).status_code, 404, name)
        page = self.client.get(reverse("nanopore:screening-create"))
        self.assertNotIn(self.b.site, list(page.context["form"].fields["site"].queryset))

    def test_posted_screening_must_be_inside_the_assignment(self):
        page = self.client.post(reverse("nanopore:diagnosis-create"), {"screening": self.b.pk})
        self.assertIn("screening", page.context["form"].errors)
        self.assertFalse(Diagnosis.objects.filter(screening=self.b).exists())

    def test_regimen_changes_outside_the_assignment_are_refused(self):
        regimen = RegimenChanges.objects.create(screening=self.b, date=date(2025, 5, 1), drug="X")
        self.assertEqual(self.client.post(reverse("nanopore:regimen-save"), {"regimen_id": regimen.pk}).status_code, 404)
        self.client.delete(reverse("nanopore:regimen-delete", args=[regimen.pk]))
        self.assertTrue(RegimenChanges.objects.filter(pk=regimen.pk).exists())

    def test_ctrl_forms_follow_the_assignment(self):
        url = reverse("nanopore:ctrl-isolate-update", args=[self.lab_b.pk])
        self.assertEqual(self.client.post(url, {"isolate_unique_lab_no": "X"}).status_code, 404)
        dar_lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        url = reverse("nanopore:ctrl-dar-nanopore", args=[dar_lab.pk])
        self.assertNotContains(self.client.get(url), 'type="submit" class="btn btn-success"')
        self.assertEqual(self.client.post(url, {"nanopore_done": self.no.pk}).status_code, 404)

    def test_inside_the_assignment_still_saves(self):
        url = reverse("nanopore:zonal-laboratory-update", args=[self.zonal_labs["A1"].pk])
        self.assertFalse(self.client.get(url).context["form"].fields["remarks"].disabled)
        self.assertNotEqual(self.client.post(url, {}).status_code, 404)

    def test_no_assignment_means_read_only(self):
        self.client.force_login(self.make_user("rev_ds_none", [access.REVIEWER, access.DATA_SPECIALIST]))
        url = reverse("nanopore:zonal-laboratory-update", args=[self.lab_b.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {}).status_code, 404)

    def test_admin_writes_everywhere_even_as_reviewer(self):
        self.client.force_login(self.make_user("rev_admin", [access.REVIEWER, access.ADMIN]))
        url = reverse("nanopore:zonal-laboratory-update", args=[self.lab_b.pk])
        self.assertNotEqual(self.client.post(url, {}).status_code, 404)

    def test_ctrl_lab_still_enters_every_zones_isolate_number(self):
        self.client.force_login(self.make_user("ctrl_rev", [access.REVIEWER, access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        self.assertEqual(self.client.get(reverse("nanopore:ctrl-isolate-update", args=[self.lab_b.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("nanopore:zonal-laboratory-update", args=[self.lab_b.pk]), {}).status_code, 404)

    def test_lists_offer_adding_only_inside_the_assignment(self):
        Screening.objects.filter(pk__in=[self.screenings["A1"].pk, self.b.pk]).update(eligible=True)
        page = self.client.get(reverse("nanopore:form-status-list")).content.decode()
        create = reverse("nanopore:enrollment-create")
        self.assertIn(f"{create}?screening={self.screenings['A1'].pk}\"", page)
        self.assertNotIn(f"{create}?screening={self.b.pk}\"", page)
