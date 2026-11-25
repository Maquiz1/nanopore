"""The Zonal Lab section hub and section 1, sample reception (nanopore/zonal_sections.py)."""
from datetime import date

from django.urls import reverse

from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.models import EdcsTblisZonal, Screening, ZonalLaboratory
from nanopore.test_data_safety import DataSafetyBase
from nanopore.zonal_sections import SECTIONS, section_cards
from options.models import (CultureMethod, LJCultureResult, CultureMicroscopyResults, MicroscopyType, NanoporeSequencingResults,
                             SampleAppearance, YesNo, YesNoNA)
from utils import access


class ZonalSectionsTests(DataSafetyBase):
    def setUp(self):
        super().setUp()
        self.purulent = SampleAppearance.objects.create(name="Purulent", value=3)
        self.new = Screening.objects.create(screening_date=date(2025, 3, 2), pid1="009", pid2="009", site=self.a1, eligible=True)
        self.lab_tech = self.make_user("lab_sections", [access.LABORATORY_TECHNICIAN], sites=[self.a1])

    def reception(self, record=None, **data):
        url = (reverse("nanopore:zonal-lab-section", args=[record.pk, "reception"]) if record
               else reverse("nanopore:zonal-lab-section-new", args=["reception"]) + f"?screening={self.new.pk}")
        return self.client.post(url, data)

    def full_reception(self, **extra):
        return {"unique_lab_no": "40001", "date_sputum_received": "2025-03-03", "appearance": self.purulent.pk,
                "sample_volume": "3", **extra}

    def statuses(self, record):
        return {card["section"].key: card["status"] for card in section_cards(record, record.screening)}

    def test_every_question_belongs_to_one_section(self):
        names = [name for section in SECTIONS for name in section.fields]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), set(ZonalLaboratoryForm.Meta.fields) - {"screening", "remarks"})

    def test_reception_starts_a_record_and_updates_edcs(self):
        self.client.force_login(self.lab_tech)
        response = self.reception(**self.full_reception())
        record = ZonalLaboratory.objects.get(screening=self.new)
        self.assertRedirects(response, reverse("nanopore:zonal-lab-hub", args=[record.pk]), fetch_redirect_response=False)
        self.assertEqual((record.unique_lab_no, record.appearance, record.created_by), ("40001", self.purulent, self.lab_tech))
        self.assertEqual(record.history.get().history_source, "Zonal Lab: Sample reception")
        self.assertTrue(EdcsTblisZonal.objects.filter(screening=self.new, unique_lab_no="40001").exists())
        statuses = self.statuses(record)
        self.assertEqual(statuses["reception"], "complete")
        self.assertEqual({statuses[key] for key in statuses if key != "reception"}, {"not_started"})

    def test_reception_needs_every_answer_and_a_reason_to_correct(self):
        self.client.force_login(self.lab_tech)
        page = self.reception(unique_lab_no="40001")
        self.assertEqual(set(page.context["form"].errors), {"date_sputum_received", "appearance", "sample_volume"})
        self.reception(**self.full_reception())
        record = ZonalLaboratory.objects.get(screening=self.new)
        page = self.reception(record, **self.full_reception(sample_volume="4"))
        self.assertIn("reason_for_change", page.context["form"].errors)
        self.reception(record, **self.full_reception(sample_volume="4", reason_for_change="Measured again"))
        record.refresh_from_db()
        self.assertEqual((float(record.sample_volume), record.history.first().history_change_reason), (4.0, "Measured again"))

    def test_dar_takes_only_the_lab_number(self):
        ctrl = self.make_user("ctrl_sections", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl])
        self.client.force_login(ctrl)
        url = reverse("nanopore:zonal-lab-section-new", args=["reception"]) + f"?screening={self.dar.pk}"
        self.assertEqual(list(self.client.get(url).context["form"].fields), ["unique_lab_no", "reason_for_change"])
        self.client.post(url, {"unique_lab_no": "30001"})
        record = ZonalLaboratory.objects.get(screening=self.dar)
        statuses = self.statuses(record)
        self.assertEqual(statuses["reception"], "complete")
        self.assertEqual({statuses[key] for key in ("microscopy", "culture", "isolate", "xpert")}, {"from_tblis"})
        page = self.client.get(reverse("nanopore:zonal-lab-hub", args=[record.pk]))
        self.assertContains(page, reverse("nanopore:ctrl-dar-nanopore", args=[record.pk]))

    def test_open_queries_show_on_their_section(self):
        lab = self.zonal_labs["A1"]  # culture performed, nothing else
        statuses = self.statuses(lab)
        self.assertEqual(statuses["reception"], "in_progress")
        cards = {card["section"].key: card for card in section_cards(lab, lab.screening)}
        self.assertIn("Missing date sputum received", cards["reception"]["queries"])

    def test_isolate_waits_for_ctrl_then_dst(self):
        lab = self.zonal_labs["A1"]
        lab.culture_isolate = YesNoNA.objects.create(pk=1, name="Yes", value=1)
        lab.isolate_date = date(2025, 4, 1)
        lab.save()
        self.assertEqual(self.statuses(lab)["isolate"], "waiting_ctrl")
        lab.isolate_unique_lab_no = "ISO-1"
        lab.save()
        self.assertEqual(self.statuses(lab)["isolate"], "waiting_dst")

    def test_access(self):
        lab = self.zonal_labs["A1"]
        hub = reverse("nanopore:zonal-lab-hub", args=[lab.pk])
        section = reverse("nanopore:zonal-lab-section", args=[lab.pk, "reception"])
        self.client.force_login(self.make_user("rev_sections", [access.REVIEWER]))
        self.assertEqual(self.client.get(hub).status_code, 200)
        self.assertNotContains(self.client.get(section), "fa-floppy-disk")
        self.assertEqual(self.client.post(section, self.full_reception()).status_code, 403)
        self.client.force_login(self.make_user("lab_b", [access.LABORATORY_TECHNICIAN], sites=[self.b1]))
        self.assertEqual(self.client.get(hub).status_code, 404)
        self.client.force_login(self.make_user("nurse_sections", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(hub).status_code, 403)
        self.client.force_login(self.lab_tech)
        self.assertEqual(self.client.get(reverse("nanopore:zonal-lab-section", args=[lab.pk, "unknown"])).status_code, 404)

    def test_starting_again_opens_the_existing_record(self):
        self.client.force_login(self.lab_tech)
        url = reverse("nanopore:zonal-lab-section-new", args=["reception"]) + f"?screening={self.screenings['A1'].pk}"
        self.assertRedirects(self.client.get(url), reverse("nanopore:zonal-lab-section", args=[self.zonal_labs["A1"].pk, "reception"]),
                             fetch_redirect_response=False)


class SectionFormsTests(DataSafetyBase):
    """Sections 2-7: gates, cleared answers, the isolate rule and who sees what."""

    def setUp(self):
        super().setUp()
        self.lab = ZonalLaboratory.objects.get(pk=self.zonal_labs["A1"].pk)
        self.lab_tech = self.make_user("lab_s27", [access.LABORATORY_TECHNICIAN], sites=[self.a1])
        self.client.force_login(self.lab_tech)
        self.lj = CultureMethod.objects.create(pk=1, name="Lj", value=1)
        self.mgit = CultureMethod.objects.create(pk=2, name="Mgit", value=2)

    def post(self, key, **data):
        return self.client.post(reverse("nanopore:zonal-lab-section", args=[self.lab.pk, key]), data)

    def fresh(self):
        return ZonalLaboratory.objects.get(pk=self.lab.pk)

    def test_microscopy_needs_all_three(self):
        page = self.post("microscopy", microscopy_type=MicroscopyType.objects.create(name="Direct sputum", value=1).pk)
        self.assertEqual(set(page.context["form"].errors), {"microscopy_date", "microscopy_results"})
        self.post("microscopy", microscopy_type=1, microscopy_date="2025-03-04",
                  microscopy_results=CultureMicroscopyResults.objects.create(name="1+", value=2).pk)
        self.assertEqual(self.fresh().microscopy_date, date(2025, 3, 4))

    def test_culture_method_opens_its_results_and_clears_the_other(self):
        self.assertIn("culture_method", self.post("culture", culture_performed=self.yes.pk).context["form"].errors)
        self.post("culture", culture_performed=self.yes.pk, culture_method=[self.lj.pk, self.mgit.pk],
                  lj_inoculation_date="2025-03-05", mgit_inoculation_date="2025-03-05", reason_for_change="First entry")
        self.assertEqual(self.fresh().mgit_inoculation_date, date(2025, 3, 5))
        self.post("culture", culture_performed=self.yes.pk, culture_method=[self.lj.pk],
                  lj_inoculation_date="2025-03-05", mgit_inoculation_date="2025-03-05", reason_for_change="Only LJ was set up")
        lab = self.fresh()
        self.assertEqual((lab.lj_inoculation_date, lab.mgit_inoculation_date), (date(2025, 3, 5), None))

    def test_isolate_is_asked_after_a_positive_culture(self):
        url = reverse("nanopore:zonal-lab-section", args=[self.lab.pk, "isolate"])
        self.assertFalse(self.client.get(url).context["form"].applicable)
        self.assertEqual(self.statuses()["isolate"], "not_started")
        self.lab.lj_results = LJCultureResult.objects.create(pk=2, name="1+", value=2)
        self.lab.save()
        form = self.client.get(url).context["form"]
        self.assertEqual(list(form.fields), ["culture_isolate", "isolate_date", "reason_for_change"])
        YesNoNA.objects.create(pk=1, name="Yes", value=1)
        self.assertIn("isolate_date", self.post("isolate", culture_isolate=1).context["form"].errors)
        self.post("isolate", culture_isolate=1, isolate_date="2025-04-01")
        self.assertEqual(self.statuses()["isolate"], "waiting_ctrl")
        self.lab.lj_results = LJCultureResult.objects.create(pk=5, name="Negative", value=5)
        self.lab.save()
        self.assertEqual(self.statuses()["isolate"], "not_applicable")

    def test_microscopy_not_applicable_without_culture(self):
        self.lab.culture_performed = self.no
        self.lab.save()
        self.assertEqual(self.statuses()["microscopy"], "not_applicable")

    def test_a_no_clears_what_it_hid(self):
        self.post("xpert", xpert_xdr_performed=self.yes.pk)
        self.assertIn("xpert_xdr_date_performed", self.post("xpert", xpert_xdr_performed=self.yes.pk).context["form"].errors)
        self.post("xpert", xpert_xdr_performed=self.yes.pk, xpert_xdr_date_performed="2025-05-01")
        self.post("xpert", xpert_xdr_performed=self.no.pk, xpert_xdr_date_performed="2025-05-01", reason_for_change="Not run")
        self.assertEqual((self.fresh().xpert_xdr_performed, self.fresh().xpert_xdr_date_performed), (self.no, None))

    def test_lpa_lines_follow_lpa(self):
        self.assertEqual(set(self.post("lpa", lpa=self.yes.pk).context["form"].errors), {"first_line_lpa", "second_line_lpa"})
        self.post("lpa", lpa=self.yes.pk, first_line_lpa=self.yes.pk, second_line_lpa=self.no.pk,
                  first_line_lpa_date="2025-05-02", second_line_lpa_date="2025-05-02")
        lab = self.fresh()
        self.assertEqual((lab.first_line_lpa_date, lab.second_line_lpa_date), (date(2025, 5, 2), None))

    def test_nanopore_uses_the_ctrl_rules(self):
        NanoporeSequencingResults.objects.create(pk=1, name="MTBC", value=1)
        self.assertIn("nanopore_sequencing_date", self.post("nanopore", nanopore_done=self.yes.pk).context["form"].errors)
        self.post("nanopore", nanopore_done=self.no.pk)
        self.assertEqual(self.fresh().nanopore_done, self.no)

    def test_dar_sections_go_to_tblis_or_ctrl(self):
        dar_lab = ZonalLaboratory.objects.create(screening=self.dar, unique_lab_no="30001")
        self.client.force_login(self.make_user("ctrl_s27", [access.LABORATORY_TECHNICIAN], sites=[self.ctrl]))
        go = lambda key: self.client.get(reverse("nanopore:zonal-lab-section", args=[dar_lab.pk, key]))
        self.assertRedirects(go("nanopore"), reverse("nanopore:ctrl-dar-nanopore", args=[dar_lab.pk]), fetch_redirect_response=False)
        self.assertRedirects(go("culture"), reverse("nanopore:zonal-lab-hub", args=[dar_lab.pk]), fetch_redirect_response=False)

    def test_view_only_users_and_edit_all(self):
        hub = reverse("nanopore:zonal-lab-hub", args=[self.lab.pk])
        self.assertNotContains(self.client.get(hub), "Edit all sections")
        self.client.force_login(self.make_user("ds_s27", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        self.assertContains(self.client.get(hub), "Edit all sections")
        self.client.force_login(self.make_user("stat_s27", [access.STATISTICIAN], zones=[self.zone_a]))
        page = self.client.get(hub)
        self.assertContains(page, "fa-eye")
        self.assertNotContains(page, "Edit all sections")
        section = reverse("nanopore:zonal-lab-section", args=[self.lab.pk, "culture"])
        self.assertTrue(all(f.disabled for f in self.client.get(section).context["form"].fields.values()))
        self.assertEqual(self.client.post(section, {"culture_performed": self.no.pk}).status_code, 403)

    def statuses(self):
        lab = self.fresh()
        return {card["section"].key: card["status"] for card in section_cards(lab, lab.screening)}


class BySectionSwitchTests(DataSafetyBase):
    """System Controls "Zonal Lab by section": where Edit and query links go."""

    def setUp(self):
        super().setUp()
        from nanopore.models.system_control import SystemControl
        self.control = SystemControl.objects.get()
        self.control.zonal_lab_by_section = True
        self.control.save()
        self.lab = self.zonal_labs["A1"]
        self.client.force_login(self.make_user("lab_switch", [access.LABORATORY_TECHNICIAN], sites=[self.a1]))
        self.edit = reverse("nanopore:zonal-laboratory-update", args=[self.lab.pk])

    def test_edit_opens_the_sections(self):
        self.assertRedirects(self.client.get(self.edit), reverse("nanopore:zonal-lab-hub", args=[self.lab.pk]), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(self.edit + "?section=culture&next=/x/"),
                             reverse("nanopore:zonal-lab-section", args=[self.lab.pk, "culture"]) + "?next=%2Fx%2F",
                             fetch_redirect_response=False)
        self.assertEqual(self.client.get(self.edit + "?all=1").status_code, 200)  # Edit all sections
        new = Screening.objects.create(screening_date=date(2025, 3, 2), pid1="010", pid2="010", site=self.a1, eligible=True)
        start = self.client.get(reverse("nanopore:zonal-laboratory-create") + f"?screening={new.pk}")
        self.assertRedirects(start, reverse("nanopore:zonal-lab-section-new", args=["reception"]) + f"?screening={new.pk}",
                             fetch_redirect_response=False)

    def test_switch_off_keeps_the_full_form(self):
        self.control.zonal_lab_by_section = False
        self.control.save()
        self.assertEqual(self.client.get(self.edit).status_code, 200)

    def test_query_links_open_the_section_and_come_back(self):
        listing = self.client.get(reverse("reports:zonal_quality_report") + "?query=missing_date_sputum_received")
        self.assertContains(listing, f"{self.edit}?section=reception&next=")
        back = reverse("reports:zonal_quality_report") + "?query=missing_date_sputum_received"
        SampleAppearance.objects.create(pk=1, name="Purulent", value=1)
        saved = self.client.post(reverse("nanopore:zonal-lab-section", args=[self.lab.pk, "reception"]),
                                 {"unique_lab_no": "LAB-A1", "date_sputum_received": "2025-03-03", "appearance": 1,
                                  "sample_volume": "2", "next": back, "reason_for_change": "Filled from the register"})
        self.assertRedirects(saved, back, fetch_redirect_response=False)

    def test_admin_turns_it_off(self):
        self.client.force_login(self.make_user("admin_switch", [access.ADMIN]))
        self.client.post(reverse("nanopore:system-controls"), {"enable_form_submissions": "on", "enable_new_screening": "on"})
        self.control.refresh_from_db()
        self.assertFalse(self.control.zonal_lab_by_section)
