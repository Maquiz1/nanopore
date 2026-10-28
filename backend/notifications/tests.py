import datetime
import re

from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from nanopore import test_access, test_dashboard
from notifications import weekly
from notifications.models import EmailLog, EmailRecipient, SiteConfiguration
from utils import access

User = test_access.User


def _link(message, path_start):
    return re.search(rf"https?://[^\s\"<]+({path_start}[^\s\"<]+)", message.body).group(1)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", EMAILS_ENABLED=True)
class AccountEmailTests(test_access.AccessTestBase):
    def setUp(self):
        cache.clear()
        SiteConfiguration.objects.create(name="Live", site_url="https://dream.example.org/")
        self.admin = User.objects.create_superuser("root", "root@example.org", "pw")

    def test_new_account_gets_activation_link_and_chooses_password(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("users:staff_add"), {"username": "asha", "email": "asha@example.org",
                                                       "first_name": "Asha", "last_name": "M", "is_active": "on"})
        user = User.objects.get(username="asha")
        self.assertFalse(user.is_active)  # no password given: inactive until the link is used
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("https://dream.example.org/users/activate/", mail.outbox[0].body)
        self.assertNotIn("password:", mail.outbox[0].body.lower())
        self.assertTrue(EmailLog.objects.filter(recipient="asha@example.org", task_type="account_activation",
                                                status=EmailLog.SENT).exists())

        self.client.logout()
        link = _link(mail.outbox[0], "/users/activate/")
        self.client.post(link, {"new_password1": "Kilimanjaro#2026", "new_password2": "Kilimanjaro#2026"})
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        # The link works once
        self.assertContains(self.client.get(link), "no longer works")
        # Log in with the email address
        self.assertTrue(self.client.login(username="ASHA@example.org", password="Kilimanjaro#2026"))

    def test_account_without_email_shows_temporary_password_once(self):
        self.client.force_login(self.admin)
        page = self.client.post(reverse("users:staff_add"), {"username": "kito", "first_name": "K", "last_name": "T",
                                                              "is_active": "on"})
        password = page.context["password"]
        self.assertEqual(len(password), 12)
        self.client.logout()
        self.assertTrue(self.client.login(username="kito", password=password))

    def test_admin_resets_password_and_user_changes_it(self):
        user = User.objects.create_user("rehema", "rehema@example.org", "Old#pass123")
        self.client.force_login(self.admin)
        self.client.post(reverse("users:staff_reset_password", args=[user.pk]), {"action": "link"})
        self.assertIn("/users/accounts/reset/", mail.outbox[-1].body)
        page = self.client.post(reverse("users:staff_reset_password", args=[user.pk]), {"action": "temporary"})
        temporary = page.context["password"]
        user.refresh_from_db()  # the session must carry the new password's hash
        self.client.force_login(user)
        self.client.post(reverse("users:password_change"), {
            "old_password": temporary, "new_password1": "Serengeti#2026", "new_password2": "Serengeti#2026"})
        user.refresh_from_db()
        self.assertTrue(user.check_password("Serengeti#2026"))
        # A nurse cannot reset someone else's password
        self.client.force_login(self.make_user("nurse", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(reverse("users:staff_reset_password", args=[user.pk])).status_code, 403)

    def test_resend_activation(self):
        user = User.objects.create_user("juma", "juma@example.org", is_active=False)
        self.client.force_login(self.admin)
        self.client.post(reverse("users:staff_send_activation", args=[user.pk]))
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()
        # Public page answers the same for unknown addresses and sends nothing
        for email in ("juma@example.org", "nobody@example.org"):
            page = self.client.post(reverse("users:resend_activation"), {"email": email}, follow=True)
            self.assertContains(page, "If that email belongs to an account")
        self.assertEqual(len(mail.outbox), 2)

    def test_login_messages(self):
        User.objects.create_user("neema", "neema@example.org", "Right#pass1", is_active=False)
        page = self.client.post(reverse("users:login"), {"username": "neema", "password": "wrong"})
        self.assertContains(page, "Wrong username/email or password")
        page = self.client.post(reverse("users:login"), {"username": "neema@example.org", "password": "Right#pass1"})
        self.assertContains(page, "not activated yet")

    def test_password_reset_uses_site_url_and_is_logged(self):
        User.objects.create_user("baraka", "baraka@example.org", "old")
        self.client.post(reverse("users:password_reset"), {"email": "baraka@example.org"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("https://dream.example.org/users/accounts/reset/", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].subject, "Reset your DREAM Nanopore password")
        self.assertTrue(EmailLog.objects.filter(task_type="password_reset", status=EmailLog.SENT).exists())

    def test_email_pages_are_admin_only(self):
        self.client.force_login(self.admin)
        for name in ("notifications:logs", "notifications:recipients", "notifications:site_urls",
                     "notifications:recipient_add", "notifications:site_url_add"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.client.force_login(self.make_user("nurse", [access.NURSE], sites=[self.a1]))
        self.assertEqual(self.client.get(reverse("notifications:logs")).status_code, 403)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", EMAILS_ENABLED=True)
class WeeklyEmailTests(test_access.AccessTestBase):
    def setUp(self):
        cache.clear()

    def make_user(self, username, roles=(), sites=(), zones=(), position=None):
        user = super().make_user(username, roles, sites, zones, position)
        user.email = f"{username}@example.org"
        user.save()
        return user

    def test_query_email_follows_role_and_sites(self):
        # Every site has an open query: a Zonal Lab form whose fields are mostly empty
        nurse = self.make_user("nurse", [access.NURSE], sites=[self.a1])
        lab = self.make_user("lab", [access.LABORATORY_TECHNICIAN], zones=[self.zone_b])
        coordinator = self.make_user("coord", [access.COORDINATOR], zones=[self.zone_a])
        self.make_user("nosite", [access.DATA_SPECIALIST])  # no assignment: nothing to send
        EmailRecipient.objects.create(email="pi@example.org", type=EmailRecipient.BCC)

        weekly.send_weekly_query_emails(datetime.date(2025, 3, 9))
        sent = {m.to[0] if m.to else m.bcc[0]: m for m in mail.outbox}
        # The nurse gets A1's missing clinical forms, never the Zonal Lab column or another site
        self.assertNotIn("Zonal Lab", sent["nurse@example.org"].body)
        self.assertNotIn("B1", sent["nurse@example.org"].body)
        self.assertNotIn("nosite@example.org", sent)
        self.assertIn("B1", sent["lab@example.org"].body)
        self.assertNotIn("A1", sent["lab@example.org"].body)
        self.assertIn("A1", sent["coord@example.org"].body)
        self.assertNotIn("B1 (", sent["coord@example.org"].body)
        self.assertIn("pi@example.org", sent)  # all-sites copy
        # Re-running the same day sends nothing twice
        count = len(mail.outbox)
        weekly.send_weekly_query_emails(datetime.date(2025, 3, 9))
        self.assertEqual(len(mail.outbox), count)

    def test_outcome_email_lists_substudy_2_on_treatment_without_outcome(self):
        from nanopore.models import ClinicLaboratory, Diagnosis, Enrollment
        from options.models import SampleNumber, TBTreatmentStarted, XpertMTB, YesNo
        yes = YesNo.objects.get(name="Yes")
        detected = XpertMTB.objects.create(pk=2, value=2, name="Detected, high")
        started = TBTreatmentStarted.objects.create(pk=1, value=1, name="Yes")
        number = SampleNumber.objects.create(name="One", value=1)
        for site in ("A1", "B1"):
            screening = self.screenings[site]
            ClinicLaboratory.objects.create(screening=screening, sample_received=yes, number_received=number,
                                            afb_microscopy_conducted=yes, xpert_mtb_rif_conducted=yes, xpert_mtb=detected)
            Enrollment.objects.create(screening=screening, enrollment_date="2025-03-02",
                                      **test_dashboard.SubstudyTwoOutcomesTests.required_answers(Enrollment))
            Diagnosis.objects.create(screening=screening, tb_diagnosis=yes, tb_treatment=started,
                                     tb_treatment_date=datetime.date(2025, 3, 3))
        self.make_user("nurse", [access.NURSE], sites=[self.a1])
        self.make_user("clin", [access.CLINICIAN], zones=[self.zone_b])
        self.make_user("lab", [access.LABORATORY_TECHNICIAN], zones=[self.zone_a])
        self.make_user("admin2", [access.ADMIN])  # admins are not on the weekly lists

        weekly.send_weekly_outcome_emails(datetime.date(2025, 10, 5))
        sent = {m.to[0]: m for m in mail.outbox}
        self.assertEqual(set(sent), {"nurse@example.org", "clin@example.org", "lab@example.org"})
        self.assertIn(self.pid("A1"), sent["lab@example.org"].body)  # zone A covers A1
        self.assertIn(self.pid("A1"), sent["nurse@example.org"].body)
        self.assertNotIn(self.pid("B1"), sent["nurse@example.org"].body)
        self.assertIn("DUE", sent["clin@example.org"].body)  # 7 months on treatment


class ScheduleTests(test_access.AccessTestBase):
    def test_jobs_are_created_once_and_admin_changes_are_kept(self):
        from django.core.management import call_command
        from django_celery_beat.models import CrontabSchedule, PeriodicTask
        call_command("setup_email_schedules", stdout=open("/dev/null", "w"))
        job = PeriodicTask.objects.get(name="weekly_query_emails")
        self.assertEqual((job.crontab.hour, job.crontab.day_of_week), ("20", "0"))
        # An admin moves it to Monday 07:00 and pauses the other one
        job.crontab = CrontabSchedule.objects.create(minute="0", hour="7", day_of_week="1", timezone="Africa/Dar_es_Salaam")
        job.save()
        PeriodicTask.objects.filter(name="weekly_treatment_outcome_emails").update(enabled=False)
        call_command("setup_email_schedules", stdout=open("/dev/null", "w"))
        self.assertEqual(PeriodicTask.objects.get(name="weekly_query_emails").crontab.hour, "7")
        self.assertFalse(PeriodicTask.objects.get(name="weekly_treatment_outcome_emails").enabled)
        self.assertEqual(PeriodicTask.objects.filter(name__startswith="weekly_").count(), 2)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", EMAILS_ENABLED=False)
class EmailsOffTests(test_access.AccessTestBase):
    """EMAILS_ENABLED off (the default): nothing is sent, accounts get temporary passwords."""

    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser("root", "root@example.org", "pw")

    def test_account_with_email_gets_a_temporary_password(self):
        self.client.force_login(self.admin)
        page = self.client.post(reverse("users:staff_add"), {"username": "asha", "email": "asha@example.org",
                                                              "first_name": "Asha", "last_name": "M", "is_active": "on"})
        self.assertContains(page, "Emails are turned off on this server")
        password = page.context["password"]
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(EmailLog.objects.exists())
        self.client.logout()
        self.assertTrue(self.client.login(username="asha", password=password))

    def test_email_options_are_hidden_and_refused(self):
        user = User.objects.create_user("juma", "juma@example.org", "pw", is_active=False)
        self.client.force_login(self.admin)
        self.assertNotContains(self.client.get(reverse("users:staff_reset_password", args=[user.pk])), 'value="link"')
        self.client.post(reverse("users:staff_reset_password", args=[user.pk]), {"action": "link"})
        self.client.post(reverse("users:staff_send_activation", args=[user.pk]))
        self.assertEqual(len(mail.outbox), 0)
        self.client.logout()
        self.assertNotContains(self.client.get(reverse("users:login")), "Forgot password?")
        self.assertContains(self.client.get(reverse("users:password_reset")), "Emails are turned off")

    def test_weekly_jobs_send_nothing_but_keep_the_snapshot(self):
        from reports.models import QuerySnapshotRun
        self.make_user("nurse", [access.NURSE], sites=[self.a1]).__class__.objects.filter(username="nurse").update(email="n@example.org")
        self.assertEqual(weekly.send_weekly_query_emails(datetime.date(2025, 3, 9)), 0)
        self.assertEqual(weekly.send_weekly_outcome_emails(datetime.date(2025, 3, 9)), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertTrue(QuerySnapshotRun.objects.filter(snapshot_date=datetime.date(2025, 3, 9)).exists())
