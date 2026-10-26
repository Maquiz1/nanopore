"""Administration pages: Email recipients, Site URLs and Email logs (admins only)."""
import datetime

from django import forms
from django.contrib import messages
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from utils import access
from utils.access_mixins import FeatureAccessMixin

from .models import TASK_LABELS, EmailLog, EmailRecipient, SiteConfiguration


class AdminOnly(FeatureAccessMixin):
    access_feature = access.SYSTEM_ADMIN


class _Styled:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", css)


class EmailRecipientForm(_Styled, forms.ModelForm):
    class Meta:
        model = EmailRecipient
        fields = ["email", "name", "type", "is_active"]
        labels = {"type": "Copy type", "is_active": "Receives the emails"}
        help_texts = {"type": "CC: recipients see each other's address. BCC: hidden from the others."}
        widgets = {"type": forms.Select(attrs={"class": "form-select"})}


class SiteConfigurationForm(_Styled, forms.ModelForm):
    class Meta:
        model = SiteConfiguration
        fields = ["name", "site_url", "from_name", "from_email", "is_active"]
        labels = {"site_url": "Site URL", "is_active": "In use"}
        help_texts = {"is_active": "Email links use the first site in use. Turn the others off."}


# ── Shared create / edit / delete pages ─────────────────────────────────────

class _Page:
    """Titles for the shared templates."""
    title = ""
    list_url = None

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "title": self.title, "list_url": self.list_url}

    def form_valid(self, form):
        messages.success(self.request, f"{self.title.split(' ', 1)[-1].capitalize()} saved.")
        return super().form_valid(form)


class _Delete(AdminOnly, DeleteView):
    template_name = "notifications/admin/confirm_delete.html"

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "list_url": self.success_url}

    def form_valid(self, form):
        messages.success(self.request, f"{self.object} deleted.")
        return super().form_valid(form)


# ── Email recipients ────────────────────────────────────────────────────────

class EmailRecipientListView(AdminOnly, ListView):
    model = EmailRecipient
    template_name = "notifications/admin/recipients.html"
    context_object_name = "recipients"


class EmailRecipientCreateView(AdminOnly, _Page, CreateView):
    model = EmailRecipient
    form_class = EmailRecipientForm
    template_name = "notifications/admin/form.html"
    success_url = list_url = reverse_lazy("notifications:recipients")
    title = "Add email recipient"


class EmailRecipientUpdateView(AdminOnly, _Page, UpdateView):
    model = EmailRecipient
    form_class = EmailRecipientForm
    template_name = "notifications/admin/form.html"
    success_url = list_url = reverse_lazy("notifications:recipients")
    title = "Edit email recipient"


class EmailRecipientDeleteView(_Delete):
    model = EmailRecipient
    success_url = reverse_lazy("notifications:recipients")


# ── Site URLs ───────────────────────────────────────────────────────────────

class SiteConfigurationListView(AdminOnly, ListView):
    model = SiteConfiguration
    template_name = "notifications/admin/site_urls.html"
    context_object_name = "configs"

    def get_context_data(self, **kwargs):
        from .mail import from_email, site_url
        return {**super().get_context_data(**kwargs), "current_url": site_url(), "current_from": from_email()}


class SiteConfigurationCreateView(AdminOnly, _Page, CreateView):
    model = SiteConfiguration
    form_class = SiteConfigurationForm
    template_name = "notifications/admin/form.html"
    success_url = list_url = reverse_lazy("notifications:site_urls")
    title = "Add site URL"


class SiteConfigurationUpdateView(AdminOnly, _Page, UpdateView):
    model = SiteConfiguration
    form_class = SiteConfigurationForm
    template_name = "notifications/admin/form.html"
    success_url = list_url = reverse_lazy("notifications:site_urls")
    title = "Edit site URL"


class SiteConfigurationDeleteView(_Delete):
    model = SiteConfiguration
    success_url = reverse_lazy("notifications:site_urls")


# ── Email logs ──────────────────────────────────────────────────────────────



def _date(value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


class EmailLogListView(AdminOnly, ListView):
    model = EmailLog
    template_name = "notifications/admin/logs.html"
    paginate_by = 50

    def get_queryset(self):
        qs = EmailLog.objects.all()
        g = self.request.GET
        if g.get("q"):
            qs = qs.filter(Q(recipient__icontains=g["q"]) | Q(subject__icontains=g["q"]))
        if g.get("status") in (EmailLog.SENT, EmailLog.FAILED):
            qs = qs.filter(status=g["status"])
        if g.get("task") in TASK_LABELS:
            qs = qs.filter(task_type=g["task"])
        if _date(g.get("start")):
            qs = qs.filter(created_at__date__gte=_date(g["start"]))
        if _date(g.get("end")):
            qs = qs.filter(created_at__date__lte=_date(g["end"]))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = self.object_list.aggregate(
            sent=Count("id", filter=Q(status=EmailLog.SENT)), failed=Count("id", filter=Q(status=EmailLog.FAILED)))
        params = self.request.GET.copy()
        params.pop("page", None)
        return {**context, **counts, "total": counts["sent"] + counts["failed"], "tasks": TASK_LABELS,
                "filters": self.request.GET, "filter_query": params.urlencode()}
