"""
End-of-study controls (nanopore/study_lock.py has the rules):

  StudyLockEvent      every lock / reopen of the study, with its reason
  PostLockCorrection  a superuser's correction window on one participant after the lock
  RecordVerification  a form record checked by a data specialist / manager: locked until unlocked
  VerificationEvent   every verify / unlock, with its reason
  AcceptedCheck       an item on a check list confirmed as correct (reports/services/accepted.py)
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

CORRECTION_DAYS = 30


class StudyLockEvent(models.Model):
    LOCK, REOPEN = "lock", "reopen"
    action = models.CharField(max_length=10, choices=((LOCK, "Locked"), (REOPEN, "Reopened")))
    reason = models.TextField()
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-at"]


class PostLockCorrectionQuerySet(models.QuerySet):
    def open(self):
        return self.filter(closed_at__isnull=True, expires_at__gt=timezone.now())


class PostLockCorrection(models.Model):
    screening = models.ForeignKey("nanopore.Screening", on_delete=models.CASCADE, related_name="post_lock_corrections")
    reason = models.TextField()
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    opened_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    closed_at = models.DateTimeField(null=True, blank=True)

    objects = PostLockCorrectionQuerySet.as_manager()

    class Meta:
        ordering = ["-opened_at"]

    @property
    def is_open(self):
        return self.closed_at is None and self.expires_at > timezone.now()


class RecordVerification(models.Model):
    """One verified form record (form key from utils.access + its pk). Deleted when unlocked."""
    form = models.CharField(max_length=30)
    object_id = models.PositiveIntegerField()
    screening = models.ForeignKey("nanopore.Screening", on_delete=models.CASCADE, related_name="verifications")
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    verified_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["form", "object_id"], name="one_verification_per_record")]


class VerificationEvent(models.Model):
    VERIFY, UNLOCK = "verify", "unlock"
    form = models.CharField(max_length=30)
    object_id = models.PositiveIntegerField()
    screening = models.ForeignKey("nanopore.Screening", on_delete=models.CASCADE, related_name="+")
    action = models.CharField(max_length=10, choices=((VERIFY, "Verified"), (UNLOCK, "Unlocked")))
    reason = models.TextField(blank=True)
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-at"]


class AcceptedCheck(models.Model):
    """
    A record on a check list confirmed as correct as it is. It stays accepted while the
    values it was about (values / fingerprint) are unchanged; Undo sets revoked_at.
    """
    list_key = models.CharField(max_length=30)      # date_issues, dsdr, untreated, no_dst, tblis_follow_up, substudy
    check_key = models.CharField(max_length=80)     # the check on that list
    object_id = models.CharField(max_length=60)     # record pk, or a TB-LIS lab number
    screening = models.ForeignKey("nanopore.Screening", on_delete=models.CASCADE, null=True, blank=True, related_name="accepted_checks")
    zonal_lab = models.ForeignKey("nanopore.ZonalLaboratory", on_delete=models.CASCADE, null=True, blank=True,
                                  related_name="accepted_checks", help_text="Set for lab checks: TB-LIS uploads leave this record as it is")
    values = models.JSONField(default=dict, blank=True)
    fingerprint = models.CharField(max_length=64)
    reason = models.TextField()
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    accepted_at = models.DateTimeField(default=timezone.now)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-accepted_at"]
        indexes = [models.Index(fields=["list_key", "check_key", "revoked_at"])]
