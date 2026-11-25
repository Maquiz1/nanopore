"""View opens the whole form read only, with Edit for those who may change it; System Controls closes new screenings."""
from django.urls import reverse

from nanopore.models import ClinicLaboratory, Diagnosis, Enrollment
from nanopore.models.system_control import SystemControl
from nanopore.test_data_safety import DataSafetyBase
from options.models import YesNo
from utils import access


class ViewPagesTests(DataSafetyBase):
    def pages(self):
        screening = self.screenings["A1"]
        yes = YesNo.objects.get(pk=1)
        from nanopore.test_dashboard import SubstudyTwoOutcomesTests as DashboardTests
        enrollment = Enrollment.objects.create(screening=screening, enrollment_date="2025-03-02",
                                               **DashboardTests.required_answers(Enrollment))
        clinic = ClinicLaboratory.objects.create(screening=screening, **DashboardTests.required_answers(ClinicLaboratory))
        diagnosis = Diagnosis.objects.create(screening=screening, **{**DashboardTests.required_answers(Diagnosis), "tb_diagnosis": yes})
        return (("screening", screening), ("enrollment", enrollment), ("clinic-laboratory", clinic), ("diagnosis", diagnosis))

    def test_view_is_the_whole_form_read_only_with_edit_for_editors(self):
        pages = self.pages()
        self.client.force_login(self.make_user("ds_view_pages", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        for name, record in pages:
            url = reverse(f"nanopore:{name}-detail", args=[record.pk])
            page = self.client.get(url)
            self.assertEqual(page.status_code, 200, name)
            self.assertTrue(page.context["read_only"], name)
            self.assertTrue(all(f.disabled for f in page.context["form"].fields.values()), name)
            self.assertContains(page, f'href="{reverse(f"nanopore:{name}-update", args=[record.pk])}"', msg_prefix=name)
            self.assertEqual(self.client.post(url, {}).status_code, 405, name)
        self.client.force_login(self.make_user("stat_view_pages", [access.STATISTICIAN], zones=[self.zone_a]))
        for name, record in pages:
            page = self.client.get(reverse(f"nanopore:{name}-detail", args=[record.pk]))
            self.assertEqual(page.status_code, 200, name)
            self.assertNotContains(page, "btn-warning page-edit-btn", msg_prefix=name)

    def test_new_screenings_can_be_closed(self):
        self.client.force_login(self.make_user("ds_new", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        add = f'href="{reverse("nanopore:screening-create")}"'
        self.assertContains(self.client.get(reverse("nanopore:screening-list")), add)
        SystemControl.objects.update(enable_new_screening=False)
        self.assertNotContains(self.client.get(reverse("nanopore:screening-list")), add)
        self.assertRedirects(self.client.get(reverse("nanopore:screening-create")), reverse("nanopore:screening-list"),
                             fetch_redirect_response=False)
        edit = reverse("nanopore:screening-update", args=[self.screenings["A1"].pk])
        self.assertEqual(self.client.get(edit).status_code, 200)  # saved screenings stay editable

    def test_diagnosis_list_shows_the_diagnosis(self):
        self.pages()
        self.client.force_login(self.make_user("ds_dx", [access.DATA_SPECIALIST], zones=[self.zone_a]))
        page = self.client.get(reverse("nanopore:diagnosis-list"))
        self.assertContains(page, "TB diagnosed")
        self.assertContains(page, "<td>Yes</td>", html=True)
