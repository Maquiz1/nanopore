"""Zonal Lab form (non-Dar es Salaam): saving rules and visible error messages."""
from django.urls import reverse

from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.models import ZonalLaboratory
from nanopore.test_access import AccessTestBase
from options.models import SampleAppearance, YesNo
from utils import access


class ZonalFormTests(AccessTestBase):
    def setUp(self):
        self.yes = YesNo.objects.get(name="Yes")
        self.no, _ = YesNo.objects.get_or_create(pk=2, defaults={"name": "No", "value": 2})
        self.appearance = SampleAppearance.objects.create(pk=1, value=1, name="Mucoid")
        ZonalLaboratory.objects.filter(screening=self.screenings["A2"]).delete()
        self.screening = self.screenings["A2"]  # Zone A: full form

    def data(self, **overrides):
        values = {
            "screening": self.screening.pk, "date_sputum_received": "2025-03-02", "appearance": self.appearance.pk,
            "sample_volume": "3", "unique_lab_no": "NEW-A2", "culture_performed": self.no.pk,
            "xpert_xdr_performed": self.no.pk, "lpa": self.no.pk, "nanopore_done": self.no.pk,
        }
        values.update(overrides)
        return values

    def form(self, **overrides):
        return ZonalLaboratoryForm(data=self.data(**overrides), screening_instance=self.screening)

    def test_lpa_no_saves_without_first_and_second_line(self):
        form = self.form()
        self.assertTrue(form.is_valid(), form.errors)

    def test_lpa_yes_requires_first_and_second_line(self):
        form = self.form(lpa=self.yes.pk)
        self.assertFalse(form.is_valid())
        self.assertIn("first_line_lpa", form.errors)
        self.assertIn("second_line_lpa", form.errors)
        self.assertTrue(self.form(lpa=self.yes.pk, first_line_lpa=self.no.pk, second_line_lpa=self.no.pk).is_valid())

    def test_failed_save_lists_every_problem_at_the_top(self):
        self.client.force_login(self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.alab]))
        url = reverse("nanopore:zonal-laboratory-create") + f"?screening={self.screening.pk}"
        response = self.client.post(url, self.data(lpa=self.yes.pk, sample_volume=""))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ZonalLaboratory.objects.filter(screening=self.screening).exists())
        self.assertContains(response, 'id="form-error-summary"')
        self.assertContains(response, 'data-error-field="id_first_line_lpa"')  # inside a hidden section
        self.assertContains(response, 'data-error-field="id_sample_volume"')
        self.assertContains(response, "Required when LPA was performed.")

    def test_successful_save_with_lpa_no(self):
        self.client.force_login(self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.alab]))
        url = reverse("nanopore:zonal-laboratory-create") + f"?screening={self.screening.pk}"
        self.client.post(url, self.data())
        self.assertTrue(ZonalLaboratory.objects.filter(screening=self.screening, unique_lab_no="NEW-A2").exists())
