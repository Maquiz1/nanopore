from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import redirect, render
from django.views.generic import View

from nanopore import study_lock, verification
from utils import access
from utils.access import has_feature

LOCK_WORD = "LOCK"


class SystemControlsView(UserPassesTestMixin, View):
    """Form switches, the study status (nanopore/study_lock.py) and the checklist before locking."""
    template_name = "nanopore/system_controls.html"
    allowed_when_locked = True  # reopening the study is done here

    def test_func(self):
        return has_feature(self.request.user, access.SYSTEM_ADMIN)

    def context(self):
        from nanopore.models import AcceptedCheck, PostLockCorrection, StudyLockEvent, TblisUploadBatch
        from reports.services.accepted import LISTS
        control = study_lock.control()
        progress = verification.progress(self.request.user)
        accepted = {row["list_key"]: row["n"] for row in AcceptedCheck.objects.filter(revoked_at__isnull=True)
                    .values("list_key").order_by().annotate(n=Count("id"))}
        return {
            "control": control,
            "switches": [{"form": form, "field": field, "label": label, "on": getattr(control, field)}
                         for form, (field, label) in study_lock.FORM_SWITCHES.items()],
            "progress": progress,
            "unverified": sum(row["total"] - row["verified"] for row in progress),
            "accepted": [(label, accepted.get(key, 0)) for key, label in LISTS.items()],
            "last_upload": TblisUploadBatch.objects.first(),
            "open_windows": PostLockCorrection.objects.open().count(),
            "events": StudyLockEvent.objects.select_related("by")[:10],
            "form_locks": [{"form": form, "label": study_lock.form_label(form), "lock": control.locked_forms.get(form),
                            "by": User.objects.filter(pk=(control.locked_forms.get(form) or {}).get("by")).first()}
                           for form in study_lock.LOCKABLE_FORMS],
            "lock_word": LOCK_WORD,
        }

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context())

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "switches")
        control = study_lock.control()
        reason = request.POST.get("reason", "").strip()
        if action == "lock":
            if control.study_locked:
                messages.info(request, "The study is already locked.")
            elif not reason or request.POST.get("confirm", "").strip() != LOCK_WORD:
                messages.error(request, f"Give the reason and type {LOCK_WORD} to lock the study.")
            else:
                study_lock.lock_study(request.user, reason[:2000])
                messages.success(request, "The study is locked: read and export only. The nightly jobs and uploads have stopped.")
            return redirect("nanopore:system-controls")
        if action in ("lock_form", "unlock_form"):
            form = request.POST.get("form")
            if form not in study_lock.LOCKABLE_FORMS:
                messages.error(request, "Unknown form.")
            elif not reason:
                messages.error(request, "Give the reason.")
            elif action == "lock_form":
                study_lock.lock_form(request.user, form, reason[:2000])
                messages.success(request, f"The {study_lock.form_label(form)} form is locked: read only, no new records.")
            elif not request.user.is_superuser:
                messages.error(request, "Only a superuser can unlock a form.")
            else:
                study_lock.unlock_form(request.user, form, reason[:2000])
                messages.success(request, f"The {study_lock.form_label(form)} form is open again.")
            return redirect("nanopore:system-controls")
        if action == "reopen":
            if not request.user.is_superuser:
                messages.error(request, "Only a superuser can reopen a locked study.")
            elif not reason:
                messages.error(request, "Give the reason for reopening the study.")
            else:
                study_lock.reopen_study(request.user, reason[:2000])
                messages.success(request, "The study is active again.")
            return redirect("nanopore:system-controls")

        if control.study_locked:
            messages.error(request, "The study is locked: reopen it before changing the switches.")
            return redirect("nanopore:system-controls")
        # Checkboxes only send a value when checked
        control.enable_form_submissions = request.POST.get("enable_form_submissions") == "on"
        control.zonal_lab_by_section = request.POST.get("zonal_lab_by_section") == "on"
        for field, _ in study_lock.FORM_SWITCHES.values():
            setattr(control, field, request.POST.get(field) == "on")
        control.save()
        messages.success(request, "System Controls updated successfully.")
        return redirect("nanopore:system-controls")
