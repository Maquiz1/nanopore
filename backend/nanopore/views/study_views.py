"""
End-of-study pages (nanopore/study_lock.py, nanopore/verification.py):

  RecordVerifyView         Verify / Unlock a form record (its View page posts here)
  VerificationView         how much of each form is verified, and the latest verify / unlock
  PostLockCorrectionsView  superusers: correction windows on participants after the lock,
                           and every change made in them
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from nanopore import study_lock, verification
from utils import access
from utils.access_mixins import FeatureAccessMixin, SuperuserRequiredMixin


def _back(request, fallback):
    back = request.POST.get("back", "")
    if url_has_allowed_host_and_scheme(back, {request.get_host()}, request.is_secure()):
        return HttpResponseRedirect(back)
    return HttpResponseRedirect(fallback)


class RecordVerifyView(FeatureAccessMixin, View):
    access_feature = access.VERIFY_RECORDS
    http_method_names = ["post"]

    def post(self, request):
        form, pk = request.POST.get("form", ""), request.POST.get("pk", "")
        if form not in verification.MODELS or not pk.isdigit():
            raise PermissionDenied
        site = "site" if form == access.SCREENING else "screening__site"
        obj = access.scope_queryset(request.user, verification.model_of(form).objects.filter(pk=pk), site).first()
        if obj is None:
            raise PermissionDenied
        if request.POST.get("action") == "unlock":
            error = verification.unlock(request.user, form, obj, request.POST.get("reason", "").strip()[:500])
            done = "Unlocked: the record can be corrected now. Verify it again when it is done."
        else:
            error = verification.verify(request.user, form, obj)
            done = "Verified: the record is read only now."
        if error:
            messages.error(request, error)
        else:
            messages.success(request, done)
        return _back(request, reverse(verification.MODELS[form][2], args=[obj.pk]))


class VerificationView(FeatureAccessMixin, View):
    access_feature = (access.VERIFY_RECORDS, access.REPORTS)
    template_name = "nanopore/study/verification.html"

    def get(self, request):
        from nanopore.models import VerificationEvent
        events = VerificationEvent.objects.select_related("by", "screening").filter(
            screening__in=access.scope_queryset(request.user, verification.model_of(access.SCREENING).objects.all(), "site"))[:50]
        labels = {form: label for form, (_, label, _) in verification.MODELS.items()}
        rows = [{"event": e, "label": labels.get(e.form, e.form),
                 "url": reverse(verification.MODELS[e.form][2], args=[e.object_id]) if e.form in verification.MODELS else ""}
                for e in events]
        return render(request, self.template_name, {"progress": verification.progress(request.user), "events": rows})


def post_lock_changes(limit=200):
    """Every change saved in a correction window after the lock, newest first."""
    from nanopore.history import REGISTRY
    rows = []
    for records in REGISTRY:
        model = getattr(records, "cls", None)
        if model is None:
            continue
        history = model.history.model
        for entry in history.objects.filter(history_change_reason__startswith="Post-lock correction").select_related("history_user")[:limit]:
            screening = entry.pk if model.__name__ == "Screening" else getattr(entry, "screening_id", None)
            rows.append({"when": entry.history_date, "model": model._meta.verbose_name.title(), "user": entry.history_user,
                         "reason": entry.history_change_reason, "kind": entry.get_history_type_display(), "screening_id": screening,
                         "record": entry.id})
    rows.sort(key=lambda row: row["when"], reverse=True)
    return rows[:limit]


class PostLockCorrectionsView(SuperuserRequiredMixin, View):
    template_name = "nanopore/study/post_lock_corrections.html"
    allowed_when_locked = True  # opening / closing a window is how a superuser corrects after the lock

    def get(self, request):
        from nanopore.models import PostLockCorrection, Screening
        changes = post_lock_changes()
        pids = dict(Screening.objects.filter(pk__in={r["screening_id"] for r in changes if r["screening_id"]}).values_list("pk", "pid"))
        for row in changes:
            row["pid"] = pids.get(row["screening_id"], "")
        windows = PostLockCorrection.objects.select_related("screening", "opened_by", "closed_by")[:200]
        return render(request, self.template_name, {
            "windows": windows, "changes": changes, "locked": study_lock.is_locked(), "days": 30})

    def post(self, request):
        from nanopore.models import PostLockCorrection, Screening
        from django.utils import timezone
        action = request.POST.get("action")
        if action == "open":
            pid, reason = request.POST.get("pid", "").strip(), request.POST.get("reason", "").strip()
            screening = Screening.objects.filter(pid__iexact=pid).first()
            if not study_lock.is_locked():
                messages.error(request, "The study is not locked: records can be edited as usual.")
            elif screening is None:
                messages.error(request, f"No participant with PID {pid}.")
            elif not reason:
                messages.error(request, "Give the reason for the correction.")
            else:
                window, new = study_lock.open_correction_window(request.user, screening, reason[:1000])
                messages.success(request, (f"Correction window open for {screening.pid} until {timezone.localtime(window.expires_at):%d %b %Y}. "
                                           "Every change is saved with your reason.") if new
                                 else f"{screening.pid} already has an open correction window.")
        elif action == "close":
            PostLockCorrection.objects.open().filter(pk=request.POST.get("window")).update(
                closed_at=timezone.now(), closed_by=request.user)
            messages.success(request, "Correction window closed.")
        return redirect("nanopore:post-lock-corrections")
