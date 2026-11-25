# utils/access_mixins.py
from functools import wraps

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed
from django.urls import reverse

from utils.access import can_edit, can_view, get_writable_sites, has_feature, scope_queryset, writable_queryset

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class FormAccessMixin(AccessMixin):
    """
    Role + assignment enforcement for a form's views.

    access_form        form key from utils.access (e.g. SCREENING)
    access_site_field  lookup from the model to its Site
    access_write       True for views that always change data (delete, upload)
    access_is_form     True for create/update views: opening one without a pk is a create
    access_safe_post   True when POST only reads data (e.g. queues an export)
    view_only          as_view(view_only=True): the View button, the whole form greyed out
    edit_url_name      with view_model, gives a View page an Edit button for those who may change the record
    """
    access_form = None
    access_site_field = "screening__site"
    access_write = False
    access_is_form = False
    access_safe_post = False
    view_only = False
    view_model = None
    edit_url_name = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self.has_form_access(request, kwargs):
            raise PermissionDenied
        if self.access_is_form and not kwargs.get("pk") and not self.view_only:
            refused = self.refuse_new(request)
            if refused:
                return refused
        if self.view_only:
            if request.method not in SAFE_METHODS:
                return HttpResponseNotAllowed(["GET"])
            request.view_edit_url = self.view_edit_url(kwargs.get("pk"))
            request.verify_panel = self.verify_panel(kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    new_form = None  # the "allow new" switch of a create page (default: access_form)

    def refuse_new(self, request):
        """System Controls can close a form to new records (or the study is locked): saved ones stay editable."""
        from django.contrib import messages
        from django.shortcuts import redirect
        from nanopore import study_lock
        form = self.new_form or self.access_form
        if study_lock.allows_new(form):
            return None
        if study_lock.is_locked():
            messages.info(request, "The study is locked: no new records can be added.")
        else:
            messages.info(request, f"New {study_lock.form_label(form)} forms are turned off in System Controls.")
        lists = {"screening": "nanopore:screening-list", "enrollment": "nanopore:enrollment-list",
                 "clinic_lab": "nanopore:clinic-laboratory-list", "zonal_lab": "nanopore:zonal-laboratory-list",
                 "diagnosis": "nanopore:diagnosis-list"}
        return study_lock._back(request, lists.get(form, "dashboard:dashboard"))

    def verify_panel(self, pk):
        """Verified badge and the Verify / Unlock buttons of a View page (nanopore/views/verification_view.py)."""
        from nanopore import study_lock
        from utils.access import VERIFY_RECORDS
        if not pk or self.access_form not in study_lock.VERIFIABLE_FORMS:
            return None
        records = scope_queryset(self.request.user, self.view_model._default_manager.filter(pk=pk), self.access_site_field) if self.view_model else None
        if records is None or not records.exists():
            return None
        found = study_lock.verification(self.access_form, pk)
        return {"form": self.access_form, "pk": pk, "verified": found,
                "may_verify": has_feature(self.request.user, VERIFY_RECORDS) and not study_lock.is_locked()}

    def view_edit_url(self, pk):
        """The Edit button of a View page (base.html), when this user may change the record."""
        if not (pk and self.view_model and self.edit_url_name and can_edit(self.request.user, self.access_form)):
            return None
        records = self.view_model._default_manager.filter(pk=pk)
        if not writable_queryset(self.request.user, records, self.access_site_field).exists():
            return None
        from nanopore import study_lock
        if study_lock.edit_block(self.request.user, self.access_form, records.first()):
            return None  # verified, or the study is locked
        return reverse(self.edit_url_name, args=[pk])

    def needs_edit(self, request, kwargs):
        return bool(
            self.access_write
            or (request.method not in SAFE_METHODS and not (self.access_safe_post and request.method == "POST"))
            or (self.access_is_form and not kwargs.get("pk"))
        )

    def has_form_access(self, request, kwargs):
        check = can_edit if self.needs_edit(request, kwargs) else can_view
        return check(request.user, self.access_form)

    def scope(self, qs, site_field=None):
        """The records this request may use: those the user may change when it writes, else those they may see."""
        limit = writable_queryset if self.needs_edit(self.request, self.kwargs) else scope_queryset
        return limit(self.request.user, qs, site_field or self.access_site_field)

    def is_read_only(self, obj=None):
        """The form opens greyed out: no edit role, or a saved record outside the user's assignment."""
        if self.view_only:
            return True
        if not can_edit(self.request.user, self.access_form):
            return True
        if obj is None:
            return False
        records = type(obj)._default_manager.filter(pk=obj.pk)
        if not writable_queryset(self.request.user, records, self.access_site_field).exists():
            return True
        from nanopore import study_lock
        block = study_lock.edit_block(self.request.user, self.access_form, obj) if obj.pk else None
        if block:
            self.request.record_notice = block  # shown at the top of the form (base.html)
            return True
        return False

    def limit_choices(self, form):
        """Restrict a form's screening/site dropdowns so out-of-scope values fail validation."""
        if "screening" in form.fields and hasattr(form.fields["screening"], "queryset"):
            field = form.fields["screening"]
            field.queryset = writable_queryset(self.request.user, field.queryset, "site")
        if "site" in form.fields and hasattr(form.fields["site"], "queryset"):
            sites = get_writable_sites(self.request.user)
            if sites is not None:
                form.fields["site"].queryset = form.fields["site"].queryset.filter(pk__in=sites)
        return form

    def get_queryset(self):
        # Detail / delete / list views resolve objects through this, so records
        # outside the user's sites return 404.
        return self.scope(super().get_queryset())


class FeatureAccessMixin(AccessMixin):
    """
    Restrict a view to users holding a feature (utils.access REPORTS, EXPORTS, ...).
    access_feature may be a tuple: holding any one of them is enough.
    """
    access_feature = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        features = self.access_feature if isinstance(self.access_feature, tuple) else (self.access_feature,)
        if not any(has_feature(request.user, feature) for feature in features):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AnyFormAccessMixin(AccessMixin):
    """Allow users who can view at least one of access_forms (e.g. data-quality pages)."""
    access_forms = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not any(can_view(request.user, form) for form in self.access_forms):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


def _login_redirect(request):
    return redirect_to_login(request.get_full_path())


def require_feature(feature):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _login_redirect(request)
            if not has_feature(request.user, feature):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


def require_form(form, write=False):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _login_redirect(request)
            needs_edit = write or request.method not in SAFE_METHODS
            if not (can_edit if needs_edit else can_view)(request.user, form):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


class SoftDeleteMixin(FormAccessMixin):
    """
    Delete view that moves the record (and what depends on it) to the recycle bin.
    Admins only; the record must still be inside the admin's scope.
    """
    template_name = "nanopore/recycle_bin/confirm_delete.html"
    success_url = None

    def has_form_access(self, request, kwargs):
        from utils.access import DELETE_RECORDS
        return has_feature(request.user, DELETE_RECORDS) and can_view(request.user, self.access_form)

    def get_context_data(self, **kwargs):
        from nanopore.recycle_bin import collect, summarize
        context = super().get_context_data(**kwargs)
        context["to_delete"] = summarize(collect(self.object))
        context["model_label"] = self.object._meta.verbose_name.title()
        context["cancel_url"] = self.request.META.get("HTTP_REFERER") or self.get_success_url()
        return context

    def get_success_url(self):
        # ?next= sends the user back to the page they deleted from (e.g. a query list)
        from django.utils.http import url_has_allowed_host_and_scheme
        next_url = self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, {self.request.get_host()}, self.request.is_secure()):
            return next_url
        return super().get_success_url()

    def form_valid(self, form):
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        from nanopore.recycle_bin import soft_delete
        entry = soft_delete(self.object, self.request.user, reason=self.request.POST.get("reason", "").strip())
        messages.success(
            self.request,
            f"{entry.model_name} {entry.pid} moved to the Recycle Bin "
            f"({entry.total_records} record(s)). An admin can restore it.",
        )
        return HttpResponseRedirect(self.get_success_url())


class SuperuserRequiredMixin(AccessMixin):
    """Superusers only (user accounts and their roles)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class OwnProfileOrSuperuserMixin(AccessMixin):
    """A user may open their own profile; superusers may open anyone's."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or str(kwargs.get("pk")) == str(request.user.pk)):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
