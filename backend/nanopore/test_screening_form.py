from datetime import date

from django.urls import reverse

from demographic.models import Sex
from locations.models import District, Region, Site, Zone
from nanopore import test_access
from nanopore.models import Screening
from options.models import EnrolledReason, YesNo

User = test_access.User


class ScreeningFormTests(test_access.AccessTestBase):
    """Dar es Salaam answers question 4 (symptoms), other zones 4(a) (GeneXpert)."""

    def setUp(self):
        self.yes = YesNo.objects.get(name="Yes")
        self.no, _ = YesNo.objects.get_or_create(name="No", defaults={"value": 2})
        self.sex = Sex.objects.create(name="Male", value=1)
        EnrolledReason.objects.create(value=1, name="Patient not eligible")
        dar = Zone.objects.create(name="Dar es Salaam", country=self.zone_a.country)
        region = Region.objects.create(name="Dar region", country=dar.country, zone=dar)
        self.dar_site = Site.objects.create(name="DAR1", pid_prefix="D1-", site_level=self.a1.site_level,
                                            district=District.objects.create(name="Ilala", region=region))
        self.client.force_login(User.objects.create_superuser("root", "root@example.org", "pw"))

    def post(self, screening, **answers):
        data = {"screening_date": "2025-03-01", "pid1": screening.pid1, "pid2": screening.pid1, "sex": self.sex.pk,
                "age": 30, "produce_resp_sample": self.yes.pk, "age18years": self.yes.pk, "consent": self.yes.pk,
                "consent_date": "2025-03-01", "not_willing": self.no.pk, "unable_understand": self.no.pk,
                "enrolled": self.yes.pk, "site": screening.site_id}
        data.update(answers)
        return self.client.post(reverse("nanopore:screening-update", args=[screening.pk]), data)

    def test_each_zone_keeps_only_its_question(self):
        dar = Screening.objects.create(screening_date=date(2025, 3, 1), pid1="002", pid2="002", site=self.dar_site)
        page = self.client.get(reverse("nanopore:screening-update", args=[dar.pk]))
        self.assertContains(page, 'name="present_symptoms"')
        self.assertNotContains(page, 'name="genexpert_confirmation"')
        # A GeneXpert answer sent for a Dar es Salaam record is dropped; date of birth alone is enough
        self.post(dar, present_symptoms=self.yes.pk, genexpert_confirmation=self.yes.pk, age="", dob="1990-01-01")
        dar.refresh_from_db()
        self.assertIsNone(dar.genexpert_confirmation)
        self.assertTrue(dar.eligible)

        outside = self.screenings["A1"]
        page = self.client.get(reverse("nanopore:screening-update", args=[outside.pk]))
        self.assertContains(page, 'name="genexpert_confirmation"')
        self.assertNotContains(page, 'name="present_symptoms"')
        self.post(outside, genexpert_confirmation=self.yes.pk, present_symptoms=self.yes.pk)
        outside.refresh_from_db()
        self.assertIsNone(outside.present_symptoms)

    def test_not_eligible_cannot_be_enrolled(self):
        screening = self.screenings["A1"]
        page = self.post(screening, genexpert_confirmation=self.yes.pk, produce_resp_sample=self.no.pk)
        self.assertContains(page, "Not eligible, so cannot be enrolled: 5. Cannot produce a sputum sample")
        # The failed page still shows the zone's question
        self.assertContains(page, 'name="genexpert_confirmation"')

    def new_screening(self, user, **extra):
        self.client.force_login(user)
        data = {"screening_date": "2025-03-01", "pid1": "777", "pid2": "777", "sex": self.sex.pk, "age": 30,
                "produce_resp_sample": self.yes.pk, "age18years": self.yes.pk, "consent": self.yes.pk,
                "consent_date": "2025-03-01", "not_willing": self.no.pk, "unable_understand": self.no.pk,
                "enrolled": self.yes.pk, "genexpert_confirmation": self.yes.pk, "present_symptoms": self.yes.pk}
        data.update(extra)
        return self.client.post(reverse("nanopore:screening-create"), data)

    def test_nurse_screens_only_at_assigned_sites(self):
        from utils import access
        nurse = self.make_user("nurse", [access.NURSE], sites=[self.a1])
        self.client.force_login(nurse)
        page = self.client.get(reverse("nanopore:screening-create"))
        self.assertEqual([s.name for s in page.context["site_choices"]], ["A1"])
        self.assertFalse(page.context["chooses_location"])
        self.assertNotContains(page, 'id="zone-pick"')
        # Another zone's site is refused; the assigned one saves with its prefix
        self.assertEqual(self.new_screening(nurse, site=self.b1.pk).status_code, 200)
        self.assertFalse(Screening.objects.filter(pid1="777").exists())
        self.new_screening(nurse, site=self.a1.pk)
        saved = Screening.objects.get(pid1="777")
        self.assertEqual((saved.site, saved.pid), (self.a1, "A1-777"))
        self.assertIsNone(saved.present_symptoms)  # zone A is not Dar es Salaam

        # A clinician assigned to zone A picks among that zone's clinics (not the national lab)
        clinician = self.make_user("clin", [access.CLINICIAN], zones=[self.zone_a])
        self.client.force_login(clinician)
        names = {s.name for s in self.client.get(reverse("nanopore:screening-create")).context["site_choices"]}
        self.assertEqual(names, {"A1", "A2", "ALAB"})

    def test_admin_picks_zone_and_site(self):
        page = self.client.get(reverse("nanopore:screening-create"))
        self.assertTrue(page.context["chooses_location"])
        self.assertContains(page, 'id="zone-pick"')
        self.assertEqual({z.name for z in page.context["zone_choices"]}, {"Zone A", "Zone B", "Dar es Salaam"})
        # A site is required
        self.assertContains(self.new_screening(User.objects.get(username="root")), "This field is required")
        self.new_screening(User.objects.get(username="root"), site=self.dar_site.pk)
        saved = Screening.objects.get(pid1="777")
        self.assertEqual((saved.pid, saved.genexpert_confirmation), ("D1-777", None))
