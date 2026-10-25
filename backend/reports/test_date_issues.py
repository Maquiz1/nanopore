import datetime

from django.urls import reverse

from nanopore.test_access import AccessTestBase
from nanopore import test_dashboard
from reports.services.date_issues import build_checks, check_queryset, date_issue_counts
from reports.views.queries.date_issues_view import OutcomeWithoutTreatmentView
from utils import access


class DateIssuesTests(AccessTestBase):
    """Screenings from AccessTestBase are dated 1 Mar 2025."""

    def setUp(self):
        from nanopore.models import ClinicLaboratory, Diagnosis, Enrollment
        from options.models import SampleNumber, TBTreatmentOutcome, TBTreatmentStarted, XpertMTB, YesNo
        yes = YesNo.objects.get(name="Yes")
        a1 = self.screenings["A1"]
        # Enrolled the day before screening (between forms)
        self.enrollment = Enrollment.objects.create(
            screening=a1, **{**test_dashboard.SubstudyTwoOutcomesTests.required_answers(Enrollment), "enrollment_date": datetime.date(2025, 2, 28)})
        # Sample 1 received before it was collected (within the form); Xpert after screening
        ClinicLaboratory.objects.create(
            screening=a1, sample_received=yes, number_received=SampleNumber.objects.create(name="One", value=1),
            afb_microscopy_conducted=yes, xpert_mtb_rif_conducted=yes,
            xpert_mtb=XpertMTB.objects.create(pk=2, value=2, name="Detected, high"),
            date_sample1_collected=datetime.date(2025, 3, 1), date_sample1_received=datetime.date(2025, 2, 20),
            xpert_date=datetime.date(2025, 3, 5),
        )
        # Outcome recorded although treatment was not started; outcome dated before treatment
        TBTreatmentStarted.objects.create(pk=1, value=1, name="Yes")
        not_started = TBTreatmentStarted.objects.create(pk=3, value=3, name="Not started, reason (specify)")
        cured = TBTreatmentOutcome.objects.create(pk=1, value=1, name="Cured")
        Diagnosis.objects.create(screening=a1, tb_diagnosis=yes, tb_outcome2=cured, tb_treatment=not_started)
        Diagnosis.objects.create(screening=self.screenings["A2"], tb_diagnosis=yes, tb_outcome2=cured, tb_treatment_id=1,
                                 tb_treatment_date=datetime.date(2025, 3, 10), tb_outcome2_date="2025-03-02")
        # Referred elsewhere with an outcome: listed so the site confirms it with the facility
        referred = TBTreatmentStarted.objects.create(pk=2, value=2, name="Referred for treatment elsewhere")
        Diagnosis.objects.create(screening=self.screenings["B1"], tb_diagnosis=yes, tb_outcome2=cured, tb_treatment=referred,
                                 tb_facility="District hospital")
        self.admin = self.make_user("admin", [access.ADMIN])
        self.client.force_login(self.admin)

    def test_checks_find_the_conflicts(self):
        counts = date_issue_counts(self.admin)
        for key in ("enrollment_before_screening", "clinic_sample1_received_before_collected",
                    "clinic_xpert_after_screening", "diagnosis_outcome_before_treatment"):
            self.assertEqual(counts[key], 1, key)
        self.assertEqual(counts["clinic_sample1_after_screening"], 0)  # collected on the screening day is fine
        self.assertEqual(sum(counts.values()), 4)

    def test_every_check_runs_and_the_page_links_both_forms(self):
        for check in build_checks():
            check_queryset(self.admin, check).count()
        page = self.client.get(reverse("reports:date_issues", args=["enrollment_before_screening"]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, reverse("nanopore:enrollment-update", args=[self.enrollment.pk]))
        self.assertContains(page, reverse("nanopore:screening-update", args=[self.screenings["A1"].pk]))

    def test_users_see_checks_of_their_forms(self):
        tech = self.make_user("tech", [access.LABORATORY_TECHNICIAN], zones=[self.zone_a])
        forms = {key.split("_")[0] for key in date_issue_counts(tech)}
        self.assertLessEqual(forms, {"zonal", "edcs"})
        nurse = self.make_user("nurse", [access.NURSE], sites=[self.a1])
        self.assertFalse(any(key.startswith(("zonal", "edcs")) for key in date_issue_counts(nurse)))

    def test_outcome_without_treatment(self):
        records = OutcomeWithoutTreatmentView.records(self.admin)
        self.assertEqual(sorted(s.pid for s in records), sorted([self.screenings["A1"].pid, self.screenings["B1"].pid]))
        self.assertEqual(records.get(pk=self.screenings["A1"].pk).substudy, "Substudy 2")
        page = self.client.get(reverse("reports:outcome_without_treatment"))
        self.assertEqual(page.context["counts"]["Substudy 2"], 1)
        self.assertContains(page, "To District hospital")
