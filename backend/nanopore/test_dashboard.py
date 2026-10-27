"""Dashboard shows each role the sections its forms allow."""
from django.urls import reverse
from nanopore.test_access import AccessTestBase
from utils import access

class DashboardSectionsTests(AccessTestBase):
    def test_each_role_sees_the_right_sections(self):
        cases = [
            ([access.NURSE], True, False), ([access.LABORATORY_TECHNICIAN], False, True),
            ([access.DATA_SPECIALIST], True, True), ([access.STATISTICIAN], True, True),
            ([access.REVIEWER], True, True), ([access.ADMIN], True, True),
        ]
        for roles, clinical, lab in cases:
            user = self.make_user("u_" + roles[0].lower(), roles, sites=[self.a1])
            self.client.force_login(user)
            html = self.client.get(reverse("dashboard:dashboard")).content.decode()
            self.assertEqual("Enrollment against targets" in html, clinical, roles)
            self.assertEqual("Zonal laboratory pipeline" in html, lab, roles)


class SubstudyTwoOutcomesTests(AccessTestBase):
    @staticmethod
    def required_answers(model):
        """An option for every required answer field (option tables need name and value)."""
        import datetime
        from django.db import models
        answers = {}
        for field in model._meta.concrete_fields:
            if field.null or field.has_default() or field.primary_key or field.name in ("screening", "enrollment_date"):
                continue
            if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                continue
            if field.is_relation:
                option = field.related_model.objects.first()
                if option is None:
                    option = field.related_model.objects.create(name=f"{field.name} 1", value=900 + len(answers))
                answers[field.name] = option
            elif isinstance(field, models.DateField):
                answers[field.name] = datetime.date(2025, 3, 2)
            elif isinstance(field, (models.IntegerField, models.DecimalField, models.FloatField)):
                answers[field.name] = 0
            elif isinstance(field, models.CharField):
                answers[field.name] = "x"
        return answers

    def test_outcomes_only_count_substudy_2_enrolled(self):
        from nanopore.models import ClinicLaboratory, Diagnosis, Enrollment
        from options.models import SampleNumber, TBTreatmentOutcome, XpertMTB, YesNo
        yes = YesNo.objects.get(name="Yes")
        cured = TBTreatmentOutcome.objects.create(pk=1, value=1, name="Cured")
        detected = XpertMTB.objects.create(pk=2, value=2, name="Detected, high")
        not_detected = XpertMTB.objects.create(pk=1, value=1, name="Not detected")
        number = SampleNumber.objects.create(name="One", value=1)
        for site, xpert in (("A1", detected), ("A2", not_detected)):
            screening = self.screenings[site]
            ClinicLaboratory.objects.create(
                screening=screening, sample_received=yes, number_received=number,
                afb_microscopy_conducted=yes, xpert_mtb_rif_conducted=yes, xpert_mtb=xpert,
            )
            Enrollment.objects.create(screening=screening, enrollment_date="2025-03-02", **self.required_answers(Enrollment))
            Diagnosis.objects.create(screening=screening, tb_diagnosis=yes, tb_outcome2=cured)
        self.client.force_login(self.make_user("admin", [access.ADMIN]))
        context = self.client.get(reverse("dashboard:dashboard")).context
        self.assertEqual(context["substudy2_enrolled_count"], 1)
        self.assertEqual(context["diagnosis_outcome_count"], 1)  # the Substudy 4 outcome is not counted
        self.assertEqual(context["diagnosis_outcome_progress"], 100.0)


class SubstudyConsistencyTests(AccessTestBase):
    """Every page groups participants the same way (nanopore/substudy.py)."""

    def setUp(self):
        from nanopore.models import ClinicLaboratory, Enrollment, Screening
        from options.models import SampleNumber, XpertMTB, YesNo
        yes = YesNo.objects.get(name="Yes")
        no = YesNo.objects.create(pk=2, name="No", value=2)
        detected = XpertMTB.objects.create(pk=2, value=2, name="Detected, high")
        not_detected = XpertMTB.objects.create(pk=1, value=1, name="Not detected")
        number = SampleNumber.objects.create(name="One", value=1)
        # pid1 -> (Xpert conducted, Xpert result); None = no Clinic Lab form at all
        participants = {
            "001": (yes, detected),      # Substudy 2
            "002": (yes, not_detected),  # Substudy 4
            "003": (no, None),           # Substudy 4: Xpert not done
            "004": (yes, None),          # Uncategorized: no result yet
            "005": None,                 # Uncategorized: no Clinic Lab
        }
        self.screening_ids = {}
        for pid1, xpert in participants.items():
            screening = self.screenings["A1"] if pid1 == "001" else Screening.objects.create(
                screening_date="2025-03-01", pid1=pid1, pid2=pid1, site=self.a1, eligible=True,
            )
            self.screening_ids[pid1] = screening.pk
            if xpert:
                ClinicLaboratory.objects.create(
                    screening=screening, sample_received=yes, number_received=number,
                    afb_microscopy_conducted=yes, xpert_mtb_rif_conducted=xpert[0], xpert_mtb=xpert[1],
                )
            Enrollment.objects.create(screening=screening, enrollment_date="2025-03-02",
                                      **SubstudyTwoOutcomesTests.required_answers(Enrollment))
        self.client.force_login(self.make_user("admin", [access.ADMIN]))

    def test_query_and_python_rules_agree(self):
        from nanopore.models import Screening
        from nanopore.substudy import SUBSTUDY_2, SUBSTUDY_4, UNCATEGORIZED, clinic_lab_of, substudy_case, substudy_of
        expected = {"001": SUBSTUDY_2, "002": SUBSTUDY_4, "003": SUBSTUDY_4, "004": UNCATEGORIZED, "005": UNCATEGORIZED}
        rows = Screening.objects.filter(pk__in=self.screening_ids.values()).annotate(group=substudy_case())
        for screening in rows:
            pid1 = next(k for k, v in self.screening_ids.items() if v == screening.pk)
            self.assertEqual(screening.group, expected[pid1], pid1)
            self.assertEqual(substudy_of(clinic_lab_of(screening)), expected[pid1], pid1)

    def test_pages_count_the_same_participants(self):
        dashboard = self.client.get(reverse("dashboard:dashboard")).context
        self.assertEqual(dashboard["substudy2_enrolled_count"], 1)
        self.assertEqual(dashboard["substudy4_enrolled_count"], 2)

        summary = self.client.get(reverse("reports:enrollment-summary")).context
        self.assertEqual((summary["substudy2_count"], summary["substudy4_count"]), (1, 2))
        site = next(row for row in summary["site_summary"] if row["screening__site__name"] == "A1")
        self.assertEqual((site["substudy2"], site["substudy4"], site["uncategorized"]), (1, 2, 2))

        for key, count in (("substudy2", 1), ("substudy4", 2), ("uncategorized", 2)):
            page = self.client.get(reverse("nanopore:form-status-list"), {"substudy": key}).context
            ids = {s.pk for s in page["paginator"].object_list} & set(self.screening_ids.values())
            self.assertEqual(len(ids), count, key)


class FormStatusListTests(AccessTestBase):
    def test_tabs_counts_and_filters_keep_the_list(self):
        from nanopore.models import Enrollment
        Enrollment.objects.create(screening=self.screenings["A1"], enrollment_date="2025-03-02",
                                  **SubstudyTwoOutcomesTests.required_answers(Enrollment))
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.create_superuser("root", "root@example.org", "pw"))
        page = self.client.get(reverse("nanopore:enrolled-list"), {"list_type": "enrolled"})
        self.assertEqual(page.context["page_title"], "Enrolled participants")
        self.assertEqual(page.context["paginator"].count, 1)
        self.assertEqual({t["key"]: t["count"] for t in page.context["tabs"]}, {"screened": 3, "eligible": 0, "enrolled": 1, "completed": 0})
        # The filter form keeps the tab, and a start date works without an end date
        self.assertContains(page, '<input type="hidden" name="list_type" value="enrolled">')
        page = self.client.get(reverse("nanopore:form-status-list"), {"start_date": "2025-03-01"})
        self.assertEqual(page.context["paginator"].count, 3)
        self.assertEqual(self.client.get(reverse("nanopore:form-status-list"), {"start_date": "2025-03-02"}).context["paginator"].count, 0)

    def test_dashboard_cards_open_the_matching_list(self):
        from django.contrib.auth.models import User
        self.client.force_login(User.objects.create_superuser("root2", "root2@example.org", "pw"))
        params = {"zone": self.zone_a.pk, "start_date": "2025-03-01"}
        dashboard = self.client.get(reverse("dashboard:dashboard"), params)
        link = reverse("nanopore:form-status-list") + f"?list_type=eligible&amp;zone={self.zone_a.pk}&amp;start_date=2025-03-01"
        self.assertContains(dashboard, link)
        tabs = {t["key"]: t["count"] for t in self.client.get(
            reverse("nanopore:form-status-list"), {"list_type": "eligible", **params}).context["tabs"]}
        self.assertEqual(tabs["screened"], dashboard.context["screened_count"])
        self.assertEqual(tabs["eligible"], dashboard.context["eligible_count"])
        self.assertEqual(tabs["enrolled"], dashboard.context["enrolled_count"])


class MasterDataTests(AccessTestBase):
    def test_status_filters_split_everyone_and_lab_tech_sees_lab_columns(self):
        from django.contrib.auth.models import User
        from nanopore.views.master_data_list import COLUMNS
        self.client.force_login(User.objects.create_superuser("root", "root@example.org", "pw"))
        url = reverse("nanopore:master-data-list")
        page = self.client.get(url)
        total = page.context["paginator"].count
        self.assertEqual(total, 3)
        for key, *_ in COLUMNS:
            statuses = ["Yes", "No", "N/F"] if key == "tblis_raw" else ["Yes", "No", "N/R", "N/A", "WAIT"]
            split = sum(self.client.get(url, {"form": key, "hint": s}).context["paginator"].count for s in statuses)
            self.assertEqual(split, total, key)
        # Filters stay in the pager links (encoded)
        self.assertEqual(self.client.get(url, {"substudy": "Substudy 4"}).context["query_params"], "substudy=Substudy+4")
        lab = self.make_user("lab", [access.LABORATORY_TECHNICIAN], sites=[self.a1])
        self.client.force_login(lab)
        labels = [c["label"] for c in self.client.get(url).context["columns"]]
        self.assertEqual(labels, ["Zonal Lab", "EDCS TB-LIS", "TB-LIS raw"])
