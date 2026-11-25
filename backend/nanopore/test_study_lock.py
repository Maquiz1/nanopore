"""Study lock, per-form switches, verified records, accepted checks (nanopore/study_lock.py, reports/services/accepted.py)."""
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from nanopore import study_lock, verification
from nanopore.models import AcceptedCheck, PostLockCorrection, RecordVerification, Screening, StudyLockEvent
from nanopore.models.system_control import SystemControl
from nanopore.test_data_safety import DataSafetyBase
from reports.services import accepted as acc
from reports.services.missing_form_dq_counts import get_missing_forms_counts
from reports.services.substudy_queries import QUERIES_BY_KEY, substudy_query_qs
from utils import access


def screening_post(screening, **changes):
    return {"site": screening.site_id, "screening_date": "2025-03-01", "pid1": screening.pid1, "pid2": screening.pid2, **changes}


class FormSwitchTests(DataSafetyBase):
    def test_a_closed_form_hides_add_refuses_create_and_stops_its_missing_count(self):
        user = self.make_user("ds_switch", [access.DATA_SPECIALIST], zones=[self.zone_a])
        Screening.objects.update(eligible=True)
        self.client.force_login(user)
        add = reverse("nanopore:enrollment-create")
        self.assertContains(self.client.get(reverse("nanopore:enrollment-list")), f'href="{add}"')
        self.assertTrue(get_missing_forms_counts(user)["missing_enrollment_count"])
        clinic_before = get_missing_forms_counts(user)["missing_clinic_count"]

        SystemControl.objects.update(allow_new_enrollment=False)
        self.assertNotContains(self.client.get(reverse("nanopore:enrollment-list")), f'href="{add}"')
        self.assertRedirects(self.client.get(add), reverse("nanopore:enrollment-list"), fetch_redirect_response=False)
        self.assertEqual(get_missing_forms_counts(user)["missing_enrollment_count"], 0)
        self.assertEqual(get_missing_forms_counts(user)["missing_clinic_count"], clinic_before)  # other forms unchanged

    def test_switches_are_saved_from_system_controls(self):
        admin = User.objects.create_superuser("root_switch", password="pw")
        self.client.force_login(admin)
        on = {field: "on" for field, _ in study_lock.FORM_SWITCHES.values()}
        on.pop("allow_new_regimen")
        self.client.post(reverse("nanopore:system-controls"), {**on, "enable_form_submissions": "on", "action": "switches"})
        control = SystemControl.objects.get()
        self.assertFalse(control.allow_new_regimen)
        self.assertTrue(control.allow_new_diagnosis and control.enable_new_screening)


class StudyLockTests(DataSafetyBase):
    def lock(self):
        admin = User.objects.create_superuser("root_lock", password="pw")
        self.client.force_login(admin)
        self.client.post(reverse("nanopore:system-controls"), {"action": "lock", "reason": "End of study", "confirm": "LOCK"})
        self.assertTrue(SystemControl.objects.get().study_locked)
        return admin

    def test_lock_needs_the_reason_and_the_word(self):
        self.client.force_login(User.objects.create_superuser("root_word", password="pw"))
        self.client.post(reverse("nanopore:system-controls"), {"action": "lock", "reason": "End", "confirm": "yes"})
        self.assertFalse(SystemControl.objects.get().study_locked)

    def test_locked_study_is_read_only_for_everyone(self):
        self.lock()
        self.assertEqual(StudyLockEvent.objects.get().reason, "End of study")
        screening = self.screenings["A1"]
        user = self.make_user("ds_locked", [access.DATA_SPECIALIST], zones=[self.zone_a])
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("nanopore:screening-detail", args=[screening.pk])).status_code, 200)
        page = self.client.get(reverse("nanopore:screening-update", args=[screening.pk]))
        self.assertTrue(page.context["read_only"])
        self.assertContains(page, "The study is locked")
        response = self.client.post(reverse("nanopore:screening-update", args=[screening.pk]), screening_post(screening, pid2="999"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Screening.objects.get(pk=screening.pk).pid2, "001")
        self.assertRedirects(self.client.get(reverse("nanopore:screening-create")), reverse("nanopore:screening-list"),
                             fetch_redirect_response=False)
        self.assertFalse(study_lock.allows_new(access.DIAGNOSIS))

    def test_the_guard_refuses_saves_outside_requests_and_jobs_stop(self):
        self.lock()
        screening = Screening.objects.get(pk=self.screenings["A1"].pk)
        screening.pid2 = "998"
        with self.assertRaises(study_lock.StudyLocked):
            screening.save()
        from nanopore.tasks_tblis_raw import process_raw_tblis_upload, sync_zonal_laboratory_daily
        self.assertEqual(sync_zonal_laboratory_daily()["status"], "SKIPPED")
        self.assertIn("locked", process_raw_tblis_upload.apply(args=["/nonexistent.csv"]).result["file_error"])

    def test_superuser_corrects_one_participant_through_a_window(self):
        admin = self.lock()
        screening = Screening.objects.get(pk=self.screenings["A1"].pk)
        other = Screening.objects.get(pk=self.screenings["A2"].pk)
        self.client.post(reverse("nanopore:post-lock-corrections"), {"action": "open", "pid": screening.pid, "reason": "Site confirmed the date"})
        window = PostLockCorrection.objects.get()
        self.assertTrue(window.is_open)
        self.assertGreater(window.expires_at, timezone.now() + timedelta(days=29))

        token = study_lock._actor.set(admin)
        try:
            screening.pid2 = "997"
            screening.save()
            other.pid2 = "996"
            with self.assertRaises(study_lock.StudyLocked):
                other.save()
        finally:
            study_lock._actor.reset(token)
        entry = screening.history.first()
        self.assertTrue(entry.history_change_reason.startswith("Post-lock correction: Site confirmed the date"))
        self.assertContains(self.client.get(reverse("nanopore:post-lock-corrections")), "Site confirmed the date")

    def test_reopen_is_for_superusers_with_a_reason(self):
        self.lock()
        SystemControl.objects.update()
        admin_role = self.make_user("admin_reopen", [access.ADMIN])
        self.client.force_login(admin_role)
        self.client.post(reverse("nanopore:system-controls"), {"action": "reopen", "reason": "Late results"})
        self.assertTrue(SystemControl.objects.get().study_locked)
        self.client.force_login(User.objects.create_superuser("root_reopen", password="pw"))
        self.client.post(reverse("nanopore:system-controls"), {"action": "reopen", "reason": "Late results"})
        self.assertFalse(SystemControl.objects.get().study_locked)

    def test_exports_stay_allowed_and_uploads_are_refused(self):
        from nanopore.views.laboratory.edcs_tblis.edcs_tblis_csv_export_views import TriggerCsvExportView
        from nanopore.views.laboratory.edcs_tblis.tblis_raw_upload_view import TblisRawUploadView
        self.assertTrue(study_lock.allowed_when_locked(TriggerCsvExportView, "edcs-tblis-export-trigger"))
        self.assertTrue(study_lock.is_upload(TblisRawUploadView))


class VerificationTests(DataSafetyBase):
    def test_verified_record_is_read_only_until_unlocked_with_a_reason(self):
        screening = self.screenings["A1"]
        user = self.make_user("ds_verify", [access.DATA_SPECIALIST], zones=[self.zone_a])
        self.client.force_login(user)
        detail = reverse("nanopore:screening-detail", args=[screening.pk])
        self.assertContains(self.client.get(detail), "Mark verified")
        with mock.patch("nanopore.verification.open_queries", return_value=0):
            self.client.post(reverse("nanopore:record-verify"), {"form": access.SCREENING, "pk": screening.pk, "action": "verify"})
        self.assertTrue(study_lock.is_verified(access.SCREENING, screening.pk))

        page = self.client.get(detail)
        self.assertContains(page, "Verified ·")
        self.assertNotContains(page, "btn-warning page-edit-btn")
        edit = self.client.get(reverse("nanopore:screening-update", args=[screening.pk]))
        self.assertTrue(edit.context["read_only"])
        fresh = Screening.objects.get(pk=screening.pk)
        fresh.pid2 = "995"
        with self.assertRaises(study_lock.RecordLocked):
            fresh.save()

        self.client.post(reverse("nanopore:record-verify"), {"form": access.SCREENING, "pk": screening.pk, "action": "unlock"})
        self.assertTrue(study_lock.is_verified(access.SCREENING, screening.pk))  # no reason: still verified
        self.client.post(reverse("nanopore:record-verify"), {"form": access.SCREENING, "pk": screening.pk, "action": "unlock", "reason": "Wrong date"})
        self.assertFalse(study_lock.is_verified(access.SCREENING, screening.pk))
        fresh.save()

    def test_open_queries_stop_verification(self):
        user = self.make_user("ds_verify_q", [access.DATA_SPECIALIST], zones=[self.zone_a])
        with mock.patch("nanopore.verification.open_queries", return_value=2):
            error = verification.verify(user, access.SCREENING, self.screenings["A1"])
        self.assertIn("2 open queries", error)
        self.assertFalse(RecordVerification.objects.exists())

    def test_only_verifiers_verify(self):
        self.client.force_login(self.make_user("nurse_verify", [access.NURSE], sites=[self.a1]))
        response = self.client.post(reverse("nanopore:record-verify"), {"form": access.SCREENING, "pk": self.screenings["A1"].pk})
        self.assertEqual(response.status_code, 403)

    def test_uploads_leave_verified_and_accepted_lab_records(self):
        lab_a1, lab_a2 = self.zonal_labs["A1"], self.zonal_labs["A2"]
        user = self.make_user("ds_frozen", [access.DATA_SPECIALIST])
        RecordVerification.objects.create(form=access.ZONAL_LAB, object_id=lab_a1.pk, screening=lab_a1.screening, verified_by=user)
        acc.accept(user, acc.NO_DST, "others", lab_a2.pk, {"lj": None}, "No sample left", screening=lab_a2.screening, zonal_lab=lab_a2)
        frozen = study_lock.frozen_screening_ids()
        self.assertEqual(frozen, {lab_a1.screening_id, lab_a2.screening_id})
        self.assertTrue(study_lock.is_frozen(lab_a1))
        self.assertFalse(study_lock.is_frozen(self.zonal_labs["B1"]))


class AcceptedCheckTests(DataSafetyBase):
    def test_accept_takes_it_off_the_list_until_its_data_changes(self):
        user = self.make_user("ds_accept", [access.DATA_SPECIALIST], zones=[self.zone_a])
        query = QUERIES_BY_KEY["uncategorized"]
        screening = Screening.objects.create(screening_date="2025-03-01", pid1="050", pid2="050", site=self.a1, eligible=True)
        Screening.objects.filter(pk=screening.pk).update(eligible=True)  # save() works eligibility out from the answers
        self.assertTrue(substudy_query_qs(user, query).filter(pk=screening.pk).exists())

        self.client.force_login(user)
        self.client.post(reverse("reports:accept_check"), {"list": acc.SUBSTUDY, "check": "uncategorized", "oid": screening.pk,
                                                           "action": "accept", "reason": "No sample collected"})
        self.assertFalse(substudy_query_qs(user, query).filter(pk=screening.pk).exists())
        self.assertTrue(substudy_query_qs(user, query, accepted=True).filter(pk=screening.pk).exists())
        page = self.client.get(reverse("reports:substudy_queries", args=["uncategorized"]) + "?show=accepted")
        self.assertContains(page, "No sample collected")

        # The data the acceptance was about changes: it is back on the list
        AcceptedCheck.objects.update(fingerprint="changed")
        self.assertTrue(substudy_query_qs(user, query).filter(pk=screening.pk).exists())

    def test_undo_and_who_may_accept(self):
        user = self.make_user("dm_accept", [access.DATA_MANAGER], zones=[self.zone_a])
        screening = Screening.objects.create(screening_date="2025-03-01", pid1="051", pid2="051", site=self.a1, eligible=True)
        Screening.objects.filter(pk=screening.pk).update(eligible=True)  # save() works eligibility out from the answers
        self.client.force_login(user)
        data = {"list": acc.SUBSTUDY, "check": "uncategorized", "oid": screening.pk, "action": "accept", "reason": "ok"}
        self.client.post(reverse("reports:accept_check"), data)
        self.client.post(reverse("reports:accept_check"), {**data, "action": "undo"})
        self.assertFalse(AcceptedCheck.objects.filter(revoked_at__isnull=True).exists())
        self.client.force_login(self.make_user("nurse_accept", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.post(reverse("reports:accept_check"), data).status_code, 403)

    def test_items_outside_the_list_or_the_users_sites_are_refused(self):
        user = self.make_user("ds_accept_b", [access.DATA_SPECIALIST], zones=[self.zone_a])
        self.client.force_login(user)
        other_zone = Screening.objects.create(screening_date="2025-03-01", pid1="052", pid2="052", site=self.b1, eligible=True)
        Screening.objects.filter(pk=other_zone.pk).update(eligible=True)  # save() works eligibility out from the answers
        self.client.post(reverse("reports:accept_check"), {"list": acc.SUBSTUDY, "check": "uncategorized",
                                                           "oid": other_zone.pk, "action": "accept", "reason": "x"})
        self.assertFalse(AcceptedCheck.objects.exists())


class PagesRenderTests(DataSafetyBase):
    def test_changed_pages_render_on_both_tabs(self):
        self.client.force_login(User.objects.create_superuser("root_pages", password="pw"))
        urls = [reverse("reports:date_issues"), reverse("reports:dsdr_checks"), reverse("reports:outcome_without_treatment"),
                reverse("reports:no_dst"), reverse("reports:substudy_queries"), reverse("nanopore:tblis-follow-up"),
                reverse("nanopore:tblis-follow-up") + "?list=rejected"]
        for url in urls:
            for tab in ("", "show=accepted"):
                full = f"{url}{'&' if '?' in url else '?'}{tab}" if tab else url
                self.assertEqual(self.client.get(full).status_code, 200, full)
        for url in (reverse("nanopore:system-controls"), reverse("nanopore:verification"), reverse("nanopore:post-lock-corrections"),
                    reverse("nanopore:form-status-list"), reverse("dashboard:dashboard")):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        SystemControl.objects.update(study_locked=True, study_locked_at=timezone.now())
        page = self.client.get(reverse("nanopore:system-controls"))
        self.assertContains(page, "Reopen the study")
        self.assertContains(self.client.get(reverse("dashboard:dashboard")), "The study is locked")


class DeleteLockedTests(DataSafetyBase):
    def test_verified_record_and_its_participant_cannot_be_deleted(self):
        from nanopore.recycle_bin import soft_delete
        lab = self.zonal_labs["A1"]
        user = User.objects.create_superuser("root_delete", password="pw")
        RecordVerification.objects.create(form=access.ZONAL_LAB, object_id=lab.pk, screening=lab.screening, verified_by=user)
        with self.assertRaises(study_lock.RecordLocked):
            soft_delete(lab, user)
        with self.assertRaises(study_lock.RecordLocked):
            soft_delete(Screening.objects.get(pk=lab.screening_id), user)
        self.assertTrue(type(lab).objects.filter(pk=lab.pk).exists())

    def test_delete_page_refuses_a_verified_record(self):
        lab = self.zonal_labs["A1"]
        user = User.objects.create_superuser("root_delete_page", password="pw")
        RecordVerification.objects.create(form=access.ZONAL_LAB, object_id=lab.pk, screening=lab.screening, verified_by=user)
        self.client.force_login(user)
        for url in (reverse("nanopore:zonal-laboratory-delete", args=[lab.pk]), reverse("nanopore:screening-delete", args=[lab.screening_id])):
            self.assertEqual(self.client.get(url).status_code, 302, url)
            self.assertEqual(self.client.post(url, {"reason": "x"}).status_code, 302, url)
        self.assertTrue(type(lab).objects.filter(pk=lab.pk).exists())


class FormLockTests(DataSafetyBase):
    def test_a_locked_form_is_read_only_while_the_rest_goes_on(self):
        admin = User.objects.create_superuser("root_form_lock", password="pw")
        self.client.force_login(admin)
        self.client.post(reverse("nanopore:system-controls"), {"action": "lock_form", "form": access.ZONAL_LAB, "reason": "Cleaned"})
        self.assertTrue(study_lock.form_locked(access.ZONAL_LAB))
        self.assertFalse(study_lock.allows_new(access.ZONAL_LAB))
        self.assertFalse(study_lock.allows_new(study_lock.NANOPORE_RUN))
        self.assertTrue(study_lock.allows_new(access.DIAGNOSIS))
        lab = type(self.zonal_labs["A1"]).objects.get(pk=self.zonal_labs["A1"].pk)
        with self.assertRaises(study_lock.StudyLocked):
            lab.save()
        screening = Screening.objects.get(pk=lab.screening_id)
        screening.save()  # other forms stay open
        # Uploads and the sync leave every Zonal Lab record as it is
        self.assertIn(lab.screening_id, study_lock.frozen_screening_ids())
        user = self.make_user("ds_form_lock", [access.DATA_SPECIALIST], zones=[self.zone_a])
        self.client.force_login(user)
        page = self.client.get(reverse("nanopore:zonal-laboratory-update", args=[lab.pk]))
        self.assertContains(page, "Zonal Lab form is locked")
        # Only a superuser unlocks
        self.client.force_login(self.make_user("admin_form_lock", [access.ADMIN]))
        self.client.post(reverse("nanopore:system-controls"), {"action": "unlock_form", "form": access.ZONAL_LAB, "reason": "x"})
        self.assertTrue(study_lock.form_locked(access.ZONAL_LAB))
        self.client.force_login(admin)
        self.client.post(reverse("nanopore:system-controls"), {"action": "unlock_form", "form": access.ZONAL_LAB, "reason": "Late result"})
        self.assertFalse(study_lock.form_locked(access.ZONAL_LAB))
        self.assertEqual(StudyLockEvent.objects.filter(form=access.ZONAL_LAB).count(), 2)


class VerifyAllTests(DataSafetyBase):
    def test_verify_all_forms_is_all_or_nothing(self):
        screening = self.screenings["A1"]  # Screening and Zonal Lab forms
        user = self.make_user("ds_verify_all", [access.DATA_SPECIALIST], zones=[self.zone_a])
        self.client.force_login(user)
        page = self.client.get(reverse("nanopore:form-status-list"))
        self.assertContains(page, "Verify all")
        data = {"form": access.SCREENING, "pk": screening.pk, "action": "verify_all"}
        with mock.patch("nanopore.verification.open_queries", side_effect=lambda u, form, obj: 2 if form == access.ZONAL_LAB else 0):
            self.client.post(reverse("nanopore:record-verify"), data)
        self.assertFalse(RecordVerification.objects.exists())  # one form had queries: nothing verified
        with mock.patch("nanopore.verification.open_queries", return_value=0):
            self.client.post(reverse("nanopore:record-verify"), data)
        self.assertEqual(set(RecordVerification.objects.values_list("form", flat=True)), {access.SCREENING, access.ZONAL_LAB})
        self.assertEqual(verification.participant_status([screening])[screening.pk], (2, 2))
        self.assertContains(self.client.get(reverse("nanopore:form-status-list")), "2/2")

    def test_participants_filter_by_verified(self):
        a1, a2 = self.screenings["A1"], self.screenings["A2"]
        user = self.make_user("ds_verified_filter", [access.DATA_SPECIALIST], zones=[self.zone_a])
        RecordVerification.objects.create(form=access.SCREENING, object_id=a1.pk, screening=a1, verified_by=user)
        RecordVerification.objects.create(form=access.ZONAL_LAB, object_id=self.zonal_labs["A1"].pk, screening=a1, verified_by=user)
        RecordVerification.objects.create(form=access.SCREENING, object_id=a2.pk, screening=a2, verified_by=user)
        self.client.force_login(user)
        found = lambda key: {s.pk for s in self.client.get(reverse("nanopore:form-status-list") + f"?verified={key}").context["screenings"]}  # noqa: E731
        self.assertIn(a1.pk, found("all"))
        self.assertNotIn(a2.pk, found("all"))
        self.assertIn(a2.pk, found("partly"))
        self.assertNotIn(a1.pk, found("none") | found("partly"))
        self.assertTrue(found("none").isdisjoint({a1.pk, a2.pk}))


class DictionaryTests(DataSafetyBase):
    def test_nanopore_runs_are_in_the_codebook(self):
        from reports.codebook import form_codebook
        names = {row["Variable name"] for row in form_codebook("nanopore_runs")}
        self.assertTrue({"pid", "attempt", "run_date", "run_number", "nanopore_results", "failure_reason"} <= names)
        zonal = {row["Variable name"] for row in form_codebook("zonal_lab")}
        self.assertTrue({"nanopore_runs", "nanopore_first_run_date", "nanopore_final_run_date",
                         "nanopore_rerun_not_planned", "nanopore_rerun_not_planned_reason"} <= zonal)
