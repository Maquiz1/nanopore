"""
Study status, per-form switches, verified records and post-lock corrections.

Study status (System Controls)
  Active   records are added and changed as usual.
  Locked   read and export only: no new records, no changes, deletes, restores or uploads,
           and the nightly jobs stop. A superuser can still correct one participant by opening
           a correction window (PostLockCorrection, 30 days) with a reason; every change made
           in it is saved in the history with "Post-lock correction: <reason>".

Per-form switches (System Controls)
  "Allow new <form>" off: the form's Add buttons disappear and its create page refuses;
  saved records stay editable, and the form's "forms missing" count stops.

Verified records (RecordVerification)
  A data specialist / manager marks a form record Verified: it is read only for everyone
  until a verifier unlocks it with a reason. EDCS/TBLIS and Nanopore runs belong to the
  Zonal Lab record, regimen changes to the Diagnosis record. TB-LIS uploads and the nightly
  sync leave verified records as they are.

Enforcement has two layers:
  StudyLockMiddleware  refuses requests that would write (POST etc.) before the view runs.
  guard()              pre_save / pre_delete on every tracked form model: the last word,
                       which also covers Celery jobs and the admin site.
"""
import contextvars
from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models.signals import post_save, pre_delete, pre_save
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from utils import access

NANOPORE_RUN = "nanopore_run"  # the "new Nanopore run" switch (re-runs on a saved Zonal Lab)

# form key -> (SystemControl field, label)
FORM_SWITCHES = {
    access.SCREENING: ("enable_new_screening", "Screening"),
    access.ENROLLMENT: ("allow_new_enrollment", "Enrollment"),
    access.CLINIC_LAB: ("allow_new_clinic_lab", "Clinic Lab"),
    access.ZONAL_LAB: ("allow_new_zonal_lab", "Zonal Lab"),
    access.DIAGNOSIS: ("allow_new_diagnosis", "Diagnosis"),
    access.REGIMEN: ("allow_new_regimen", "Regimen changes"),
    NANOPORE_RUN: ("allow_new_nanopore_run", "Nanopore runs"),
}
# Missing-form keys (utils.access.MISSING_FORM_TYPES) whose count stops with the switch
VERIFIABLE_FORMS = (access.SCREENING, access.ENROLLMENT, access.CLINIC_LAB, access.ZONAL_LAB, access.DIAGNOSIS)

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")
DATA_NAMESPACES = {"nanopore", "reports", "clinical", "household"}
EXPORT_WORDS = ("Export", "Download", "Serve", "Trigger")
ALWAYS_ALLOWED_URLS = {"task-status", "task-revoke"}

_actor = contextvars.ContextVar("study_actor", default=None)  # the user of the current request
_memo = contextvars.ContextVar("study_memo", default=None)    # per-request cache of SystemControl


class StudyLocked(PermissionDenied):
    """A change refused: the study is locked."""


class RecordLocked(PermissionDenied):
    """A change refused: the record is verified."""


# ── Settings ────────────────────────────────────────────────────────────────

def control():
    """The SystemControl row (created on first use), read once per request."""
    from nanopore.models.system_control import SystemControl
    memo = _memo.get()
    if memo is not None and "control" in memo:
        return memo["control"]
    found = SystemControl.objects.first() or SystemControl.objects.create()
    if memo is not None:
        memo["control"] = found
    return found


def forget_control():
    memo = _memo.get()
    if memo is not None:
        memo.pop("control", None)


def is_locked():
    return control().study_locked


LOCKABLE_FORMS = (access.SCREENING, access.ENROLLMENT, access.CLINIC_LAB, access.ZONAL_LAB, access.DIAGNOSIS, access.REGIMEN)


def locked_forms():
    """{form key: {"at", "by", "reason"}} of the forms locked on their own (System Controls)."""
    return control().locked_forms or {}


def form_locked(form):
    if form == NANOPORE_RUN:
        form = access.ZONAL_LAB
    return form in locked_forms()


def record_forms(instance):
    """The forms a saved record belongs to (EDCS/TBLIS and Nanopore runs: Zonal Lab; regimen rows: Regimen and Diagnosis)."""
    from nanopore.models import RegimenChanges
    form = owner(instance)[0]
    forms = {form} if form else set()
    if isinstance(instance, RegimenChanges):
        forms.add(access.REGIMEN)
    return forms


def lock_text(forms):
    """Why records of these forms can't be changed now (None when they can)."""
    if is_locked():
        return "The study is locked: records can be viewed and exported, not changed."
    for form in forms:
        found = locked_forms().get(form)
        if found:
            return f"The {form_label(form)} form is locked (since {found.get('at', '')[:10]}): read only."
    return None


def allows_new(form):
    """May new records of this form be added now? (study active, form not locked, its switch on)"""
    c = control()
    if c.study_locked or form_locked(form):
        return False
    field = FORM_SWITCHES.get(form, (None,))[0]
    return getattr(c, field, True) if field else True


def closed_forms():
    """Form keys whose "allow new" switch is off (all of them while the study is locked)."""
    return {form for form in FORM_SWITCHES if not allows_new(form)}


def form_label(form):
    return FORM_SWITCHES.get(form, (None, form))[1]


# ── Who owns a record (verification) and its participant ───────────────────

def owner(instance):
    """(form key, record pk, screening id) of the verifiable record that instance belongs to."""
    from nanopore import models as m
    if isinstance(instance, m.Screening):
        return access.SCREENING, instance.pk, instance.pk
    for model, form in ((m.Enrollment, access.ENROLLMENT), (m.ClinicLaboratory, access.CLINIC_LAB),
                        (m.ZonalLaboratory, access.ZONAL_LAB), (m.Diagnosis, access.DIAGNOSIS)):
        if isinstance(instance, model):
            return form, instance.pk, instance.screening_id
    if isinstance(instance, m.EdcsTblisZonal):
        lab = m.ZonalLaboratory.objects.filter(screening_id=instance.screening_id).values_list("pk", flat=True).first()
        return access.ZONAL_LAB, lab, instance.screening_id
    if isinstance(instance, m.NanoporeRun):
        screening_id = m.ZonalLaboratory.objects.filter(pk=instance.zonal_lab_id).values_list("screening_id", flat=True).first()
        return access.ZONAL_LAB, instance.zonal_lab_id, screening_id
    if isinstance(instance, m.RegimenChanges):
        dx = m.Diagnosis.objects.filter(screening_id=instance.screening_id).values_list("pk", flat=True).first()
        return access.DIAGNOSIS, dx, instance.screening_id
    return None, None, None


def verification(form, pk):
    from nanopore.models import RecordVerification
    if not pk:
        return None
    return RecordVerification.objects.filter(form=form, object_id=pk).select_related("verified_by").first()


def is_verified(form, pk):
    from nanopore.models import RecordVerification
    return bool(pk) and RecordVerification.objects.filter(form=form, object_id=pk).exists()


def open_correction(screening_id):
    from nanopore.models import PostLockCorrection
    if not screening_id:
        return None
    return PostLockCorrection.objects.open().filter(screening_id=screening_id).first()


def frozen_screening_ids(screening_ids=None):
    """Participants TB-LIS uploads and the nightly sync must leave as they are: their Zonal Lab
    is verified, or a lab check on it is accepted (reports/services/accepted.py), or the whole
    Zonal Lab form is locked."""
    from nanopore.models import AcceptedCheck, RecordVerification, ZonalLaboratory
    if form_locked(access.ZONAL_LAB):
        labs = ZonalLaboratory.objects.all()
        if screening_ids is not None:
            labs = labs.filter(screening_id__in=screening_ids)
        return set(labs.values_list("screening_id", flat=True))
    verified = RecordVerification.objects.filter(form=access.ZONAL_LAB).values_list("object_id", flat=True)
    labs = ZonalLaboratory.objects.filter(pk__in=verified)
    if screening_ids is not None:
        labs = labs.filter(screening_id__in=screening_ids)
    ids = set(labs.values_list("screening_id", flat=True))
    accepted = AcceptedCheck.objects.filter(revoked_at__isnull=True, zonal_lab__isnull=False)
    if screening_ids is not None:
        accepted = accepted.filter(zonal_lab__screening_id__in=screening_ids)
    return ids | set(accepted.values_list("zonal_lab__screening_id", flat=True))


def is_frozen(lab):
    """A Zonal Lab (or its participant) that uploads and the sync must not change."""
    return bool(lab) and lab.screening_id in frozen_screening_ids([lab.screening_id])


def edit_block(user, form, obj):
    """Why this saved record opens read only for this user (None when it may be changed)."""
    pk = getattr(obj, "pk", None)
    forms = record_forms(obj) if obj is not None else set()
    if form in LOCKABLE_FORMS:
        forms.add(form)
    locked = lock_text(forms)
    if locked:
        if getattr(user, "is_superuser", False) and obj is not None and open_correction(owner(obj)[2]):
            return None
        return locked
    if form == access.EDCS_TBLIS or form == access.CTRL_ISOLATES:
        form, pk = access.ZONAL_LAB, owner(obj)[1] if obj is not None else None
    if obj is not None and form not in VERIFIABLE_FORMS:
        form, pk, _ = owner(obj)
    found = verification(form, pk)
    if found:
        return (f"Verified by {found.verified_by.get_full_name() or found.verified_by.username} on "
                f"{timezone.localtime(found.verified_at):%d %b %Y}: read only until a verifier unlocks it.")
    return None


# ── The guard on every save / delete of a form model ───────────────────────

def guard(sender, instance, **kwargs):
    if kwargs.get("raw") or getattr(instance, "_study_guard_off", False):
        return
    form, pk, screening_id = owner(instance)
    locked = lock_text(record_forms(instance))
    if locked:
        user = _actor.get()
        correction = open_correction(screening_id) if getattr(user, "is_superuser", False) else None
        if correction is None:
            raise StudyLocked(locked.replace("not changed", "not added, changed or deleted"))
        note = f"Post-lock correction: {correction.reason}"
        given = getattr(instance, "_change_reason", "")
        instance._change_reason = f"{note} | {given}" if given and note not in given else (given or note)
        return
    if form and pk and is_verified(form, pk):
        raise RecordLocked("This record is verified: a verifier must unlock it (with a reason) before it can be changed.")


def connect():
    from nanopore.history import REGISTRY
    from nanopore.models.system_control import SystemControl
    for records in REGISTRY:
        model = getattr(records, "cls", None)
        if model is not None:
            pre_save.connect(guard, sender=model, dispatch_uid=f"study_guard_save_{model.__name__}")
            pre_delete.connect(guard, sender=model, dispatch_uid=f"study_guard_delete_{model.__name__}")
    post_save.connect(lambda **kw: forget_control(), sender=SystemControl, weak=False, dispatch_uid="study_control_saved")


# ── Middleware ──────────────────────────────────────────────────────────────

def _back(request, fallback="dashboard:dashboard"):
    target = request.META.get("HTTP_REFERER", "")
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}, request.is_secure()):
        return HttpResponseRedirect(target)
    try:
        return HttpResponseRedirect(reverse(fallback))
    except Exception:
        return HttpResponseRedirect("/")


def refuse(request, text):
    wants_json = request.headers.get("x-requested-with") == "XMLHttpRequest" or "json" in request.headers.get("accept", "")
    if wants_json:
        return JsonResponse({"success": False, "error": text, "errors": {"__all__": [text]}}, status=403)
    messages.error(request, text)
    return _back(request)


def _view_class(view_func):
    return getattr(view_func, "view_class", None) or view_func


def is_upload(cls):
    return "Upload" in getattr(cls, "__name__", "") or getattr(cls, "is_upload", False)


def allowed_when_locked(cls, url_name):
    name = getattr(cls, "__name__", "")
    return bool(getattr(cls, "allowed_when_locked", False) or getattr(cls, "access_safe_post", False)
                or any(word in name for word in EXPORT_WORDS) or url_name in ALWAYS_ALLOWED_URLS)


class StudyLockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        actor = _actor.set(getattr(request, "user", None))
        memo = _memo.set({})
        try:
            return self.get_response(request)
        finally:
            _actor.reset(actor)
            _memo.reset(memo)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in SAFE_METHODS or not request.user.is_authenticated:
            return None
        match = request.resolver_match
        if not match or (match.namespace or "").split(":")[0] not in DATA_NAMESPACES:
            return None
        cls, url_name = _view_class(view_func), match.url_name
        c = control()
        if c.study_locked:
            if is_upload(cls):
                return refuse(request, "Uploads are closed: the study is locked.")
            if allowed_when_locked(cls, url_name) or request.user.is_superuser:
                return None  # superusers: guard() allows the participants with an open correction
            return refuse(request, "The study is locked: records can be viewed and exported, not changed.")
        if not c.enable_form_submissions and not request.user.is_superuser and not allowed_when_locked(cls, url_name):
            from utils.access_mixins import FormAccessMixin
            if isinstance(cls, type) and issubclass(cls, FormAccessMixin):
                return refuse(request, "Saving is turned off in System Controls.")
        return None

    def process_exception(self, request, exception):
        if isinstance(exception, (StudyLocked, RecordLocked)):
            return refuse(request, str(exception))
        return None


# ── Locking and corrections ────────────────────────────────────────────────

def lock_study(user, reason):
    from nanopore.models import StudyLockEvent
    c = control()
    # Last query snapshot before the jobs stop
    try:
        from reports.services.query_snapshot import take_snapshot
        take_snapshot()
    except Exception:
        pass
    c.study_locked, c.study_locked_at, c.study_locked_by, c.study_lock_reason = True, timezone.now(), user, reason
    c.save()
    StudyLockEvent.objects.create(action=StudyLockEvent.LOCK, reason=reason, by=user)


def reopen_study(user, reason):
    from nanopore.models import StudyLockEvent
    c = control()
    c.study_locked = False
    c.save()
    StudyLockEvent.objects.create(action=StudyLockEvent.REOPEN, reason=reason, by=user)


def lock_form(user, form, reason):
    from nanopore.models import StudyLockEvent
    c = control()
    forms = dict(c.locked_forms or {})
    forms[form] = {"at": timezone.now().isoformat(), "by": user.pk, "reason": reason}
    c.locked_forms = forms
    c.save()
    StudyLockEvent.objects.create(action=StudyLockEvent.LOCK, form=form, reason=reason, by=user)


def unlock_form(user, form, reason):
    from nanopore.models import StudyLockEvent
    c = control()
    forms = dict(c.locked_forms or {})
    forms.pop(form, None)
    c.locked_forms = forms
    c.save()
    StudyLockEvent.objects.create(action=StudyLockEvent.REOPEN, form=form, reason=reason, by=user)


def delete_block(user, objects):
    """Why these records (a record and what depends on it) can't be deleted now, or None."""
    for instance in objects:
        if getattr(instance, "pk", None) is None or not record_forms(instance):
            continue
        form, pk, screening_id = owner(instance)
        locked = lock_text(record_forms(instance))
        if locked and not (getattr(user, "is_superuser", False) and open_correction(screening_id)):
            return locked
        if form and pk and is_verified(form, pk):
            return (f"Can't delete: the {form_label(form)} record of this participant is verified. "
                    "A verifier must unlock it (with a reason) first.")
    return None


def anything_locked():
    return is_locked() or bool(locked_forms())


def open_correction_window(user, screening, reason, days=None):
    from nanopore.models import PostLockCorrection
    from nanopore.models.study_lock import CORRECTION_DAYS
    found = open_correction(screening.pk)
    if found:
        return found, False
    return PostLockCorrection.objects.create(
        screening=screening, reason=reason, opened_by=user,
        expires_at=timezone.now() + timedelta(days=days or CORRECTION_DAYS)), True


def job_allowed(name):
    """Nightly jobs and uploads stop while the study is locked."""
    if is_locked():
        import logging
        logging.getLogger(__name__).info("%s skipped: the study is locked", name)
        return False
    return True
