from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Exists, OuterRef, Q
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import ListView

from nanopore.models import Screening, TblisRawData
from nanopore.substudy import SUBSTUDY_2, SUBSTUDIES, UNCATEGORIZED, substudy_case
from utils import access
from utils.access import assigned_locations, scope_queryset
from utils.access_mixins import AnyFormAccessMixin
from utils.roles import get_role_context

# Status of one form for one participant (the "hint" filter values)
DONE, MISSING, NOT_NEEDED, EXTRA, WAITING, NOT_FOUND = "Yes", "No", "N/A", "N/R", "WAIT", "N/F"
STATUS_LABELS = {
    DONE: ("Done", "ok"),
    MISSING: ("Missing", "miss"),
    NOT_NEEDED: ("N/A", "na"),
    EXTRA: ("Not required", "extra"),
    WAITING: ("Waiting", "wait"),
    NOT_FOUND: ("No lab no.", "na"),  # no Zonal Lab form, so nothing to look up in TB-LIS
}

# column key -> (header, form whose view right shows it, related record attr, detail URL name)
COLUMNS = [
    ("enrollment", "Enrollment", access.ENROLLMENT, "enrollment", "nanopore:enrollment-detail"),
    ("clinic", "Clinic Lab", access.CLINIC_LAB, "clinic_laboratory", "nanopore:clinic-laboratory-detail"),
    ("zonal", "Zonal Lab", access.ZONAL_LAB, "zonal_laboratory", "nanopore:zonal-laboratory-detail"),
    ("diagnosis", "Diagnosis", access.DIAGNOSIS, "diagnosis", "nanopore:diagnosis-detail"),
    ("regimen", "Regimen", access.REGIMEN, None, "nanopore:diagnosis-detail"),
    ("edcs_tblis", "EDCS TB-LIS", access.EDCS_TBLIS, "tblis_laboratory", "nanopore:edcs-tblis-laboratory-view"),
    ("tblis_raw", "TB-LIS raw", access.EDCS_TBLIS, None, None),
]
FORM_RELATION = {key: rel for key, _, _, rel, _ in COLUMNS if rel}


def expected_q(form):
    """Participants who should have this form."""
    if form in ("zonal", "edcs_tblis"):
        return Q(eligible=True, substudy_case=SUBSTUDY_2)  # only Substudy 2 goes to the zonal lab
    if form == "regimen":
        return Q(eligible=True, diagnosis__regimen_changed__value=1)  # 10(a) = Yes
    return Q(eligible=True)


def has_q(form):
    if form == "regimen":
        return Q(regimen_count__gt=0)
    if form == "tblis_raw":
        return Q(has_tblis_raw=True)
    return Q(**{f"{FORM_RELATION[form]}__isnull": False})


def status_filter(form, status):
    """Q for one form + status, the same rules as cell_status()."""
    if form == "tblis_raw":
        return {DONE: Q(zonal_laboratory__isnull=False, has_tblis_raw=True),
                MISSING: Q(zonal_laboratory__isnull=False, has_tblis_raw=False),
                NOT_FOUND: Q(zonal_laboratory__isnull=True)}.get(status)
    expected, has = expected_q(form), has_q(form)
    waiting = Q(eligible=True, substudy_case=UNCATEGORIZED) if form in ("zonal", "edcs_tblis") else Q(pk__in=[])
    return {DONE: expected & has,
            MISSING: expected & ~has,
            EXTRA: ~expected & has,
            WAITING: waiting & ~has,
            NOT_NEEDED: ~expected & ~has & ~waiting}.get(status)


def related(s, name):
    """The participant's form of that kind, or None (a missing one-to-one raises otherwise)."""
    try:
        return getattr(s, name)
    except ObjectDoesNotExist:
        return None


def cell_status(s, form):
    if form == "tblis_raw":
        if related(s, "zonal_laboratory") is None:
            return NOT_FOUND
        return DONE if s.has_tblis_raw else MISSING  # lab no. not in the uploaded TB-LIS files
    if form == "regimen":
        diagnosis = related(s, "diagnosis")
        expected = bool(s.eligible and diagnosis and diagnosis.regimen_changed_id and diagnosis.regimen_changed.value == 1)
        has = s.regimen_count > 0
    else:
        has = related(s, FORM_RELATION[form]) is not None
        if form in ("zonal", "edcs_tblis"):
            if s.eligible and s.substudy_case == UNCATEGORIZED and not has:
                return WAITING
            expected = s.eligible and s.substudy_case == SUBSTUDY_2
        else:
            expected = s.eligible
    if expected:
        return DONE if has else MISSING
    return EXTRA if has else NOT_NEEDED


class MasterDataListView(AnyFormAccessMixin, ListView):
    access_forms = access.ALL_FORMS
    model = Screening
    template_name = "nanopore/master_data_list.html"
    context_object_name = "screenings"
    paginate_by = 25

    def visible_columns(self):
        user = self.request.user
        return [c for c in COLUMNS if access.can_view(user, c[2])]

    def get_queryset(self):
        qs = Screening.objects.select_related(
            "site__district__region__zone",
            "enrollment",
            "clinic_laboratory",
            "zonal_laboratory",
            "diagnosis__regimen_changed",
            "tblis_laboratory",
        ).annotate(
            substudy_case=substudy_case(),  # one definition: nanopore/substudy.py
            regimen_count=Count("regimen_changes", distinct=True),
            has_tblis_raw=Exists(TblisRawData.objects.filter(labno=OuterRef("zonal_laboratory__unique_lab_no"))),
        )
        qs = scope_queryset(self.request.user, qs, "site")

        get = lambda key: self.request.GET.get(key, "").strip()
        if get("pid_labno"):
            qs = qs.filter(Q(pid__icontains=get("pid_labno")) | Q(zonal_laboratory__unique_lab_no__icontains=get("pid_labno")))
        if get("zone"):
            qs = qs.filter(site__district__region__zone_id=get("zone"))
        if get("site"):
            qs = qs.filter(site_id=get("site"))
        if get("substudy") in SUBSTUDIES:
            qs = qs.filter(substudy_case=get("substudy"))
        if get("eligibility") == "Yes":
            qs = qs.filter(eligible=True)
        elif get("eligibility") == "No":
            qs = qs.filter(eligible=False)

        visible = {c[0] for c in self.visible_columns()}
        if get("form") in visible and get("hint"):
            q = status_filter(get("form"), get("hint"))
            if q is not None:
                qs = qs.filter(q)

        return qs.order_by("-screening_date", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context.update(get_role_context(user))
        assigned_zones, assigned_sites = assigned_locations(user)
        context.update({"assigned_zones": assigned_zones, "assigned_sites": assigned_sites})

        columns = self.visible_columns()
        context["columns"] = [{"key": c[0], "label": c[1]} for c in columns]
        rows = []
        for s in context["screenings"]:
            cells = []
            for key, label, form, rel, url_name in columns:
                status = cell_status(s, key)
                text, css = STATUS_LABELS[status]
                if key == "regimen" and s.regimen_count:
                    text = f"{text} ({s.regimen_count})" if status == DONE else text
                record = related(s, "diagnosis") if key == "regimen" else (related(s, rel) if rel else None)
                url = reverse(url_name, args=[record.pk]) if url_name and record is not None else ""
                cells.append({"label": label, "text": text, "css": css, "url": url, "status": status})
            rows.append({"s": s, "cells": cells})
        context["rows"] = rows

        selected = {key: self.request.GET.get(key, "").strip()
                    for key in ("pid_labno", "zone", "site", "substudy", "eligibility", "form", "hint")}
        context["selected"] = selected
        context["filters_active"] = any(selected.values())
        context["query_params"] = urlencode({k: v for k, v in selected.items() if v})
        context["show_location_filter"] = (context["sites"].count() if hasattr(context["sites"], "count") else len(context["sites"])) > 1
        context["substudies"] = SUBSTUDIES
        return context
