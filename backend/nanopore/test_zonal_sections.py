"""The Zonal Lab section hub and section 1, sample reception (nanopore/zonal_sections.py)."""
from datetime import date

from django.urls import reverse

from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.models import EdcsTblisZonal, Screening, ZonalLaboratory
from nanopore.test_data_safety import DataSafetyBase
from nanopore.zonal_sections import SECTIONS, section_cards
from options.models import SampleAppearance, YesNoNA
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
        self.assertEqual(self.client.get(reverse("nanopore:zonal-lab-section", args=[lab.pk, "culture"])).status_code, 404)

    def test_starting_again_opens_the_existing_record(self):
        self.client.force_login(self.lab_tech)
        url = reverse("nanopore:zonal-lab-section-new", args=["reception"]) + f"?screening={self.screenings['A1'].pk}"
        self.assertRedirects(self.client.get(url), reverse("nanopore:zonal-lab-section", args=[self.zonal_labs["A1"].pk, "reception"]),
                             fetch_redirect_response=False)
