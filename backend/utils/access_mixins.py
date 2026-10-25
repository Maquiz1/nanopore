# utils/access_mixins.py
from functools import wraps

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from utils.access import can_edit, can_view, get_accessible_sites, has_feature, scope_queryset

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class FormAccessMixin(AccessMixin):
    """
    Role + assignment enforcement for a form's views.

    access_form        form key from utils.access (e.g. SCREENING)
    access_site_field  lookup from the model to its Site
    access_write       True for views that always change data (delete, upload)
    access_is_form     True for create/update views: opening one without a pk is a create
    access_safe_post   True when POST only reads data (e.g. queues an export)
    """
    access_form = None
    access_site_field = "screening__site"
    access_write = False
    access_is_form = False
    access_safe_post = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self.has_form_access(request, kwargs):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def has_form_access(self, request, kwargs):
        needs_edit = (
            self.access_write
            or (request.method not in SAFE_METHODS and not (self.access_safe_post and request.method == "POST"))
            or (self.access_is_form and not kwargs.get("pk"))
        )
        check = can_edit if needs_edit else can_view
        return check(request.user, self.access_form)

    def scope(self, qs, site_field=None):
        return scope_queryset(self.request.user, qs, site_field or self.access_site_field)

    def limit_choices(self, form):
        """Restrict a form's screening/site dropdowns so out-of-scope values fail validation."""
        if "screening" in form.fields and hasattr(form.fields["screening"], "queryset"):
            field = form.fields["screening"]
            field.queryset = scope_queryset(self.request.user, field.queryset, "site")
        if "site" in form.fields and hasattr(form.fields["site"], "queryset"):
            sites = get_accessible_sites(self.request.user)
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
