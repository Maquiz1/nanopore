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
