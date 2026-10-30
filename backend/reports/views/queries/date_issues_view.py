# reports/views/queries/date_issues_view.py
import re
from collections import defaultdict

from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from nanopore.substudy import OUTCOMES, SUBSTUDIES, substudy_case
from reports.services import dsdr_checks
from reports.services.date_issues import STUDY_START, FORMS, check_queryset, form_record, resolve, visible_checks
from utils import access
from utils.access import can_see_queries, scope_queryset
from utils.roles import get_role_context

# form -> (edit URL name, view URL name)
FORM_URLS = {
    access.SCREENING: ("nanopore:screening-update", "nanopore:screening-detail"),
    access.ENROLLMENT: ("nanopore:enrollment-update", "nanopore:enrollment-detail"),
    access.CLINIC_LAB: ("nanopore:clinic-laboratory-update", "nanopore:clinic-laboratory-detail"),
    access.ZONAL_LAB: ("nanopore:zonal-laboratory-update", "nanopore:zonal-laboratory-detail"),
    access.EDCS_TBLIS: ("nanopore:edcs-tblis-laboratory-update", "nanopore:edcs-tblis-laboratory-view"),
    access.DIAGNOSIS: ("nanopore:diagnosis-update", "nanopore:diagnosis-detail"),
}
# Regimen changes are edited in the table on the Diagnosis form
REGIMEN_ANCHOR = "#regimen-change-section"


def _zone_site(request):
    role_context = get_role_context(request.user)
    zones = {z.id: z.name for z in role_context.get("zones", [])}
    sites = {s.id: s.name for s in role_context.get("sites", [])}

    def pick(name, allowed):
        value = request.GET.get(name, "")
        return int(value) if value.isdigit() and int(value) in allowed else None

    return zones, sites, pick("zone", zones), pick("site", sites)


def _filter_query(request):
    params = request.GET.copy()
    params.pop("page", None)
    return params.urlencode()


class DateIssuesView(LoginRequiredMixin, View):
    """Dates that are impossible within a form or conflict between forms, with links to fix them."""
    template_name = "reports/data_quality/date_issues/date_issues.html"
    paginate_by = 50
    builder = None  # list of checks; None = the date checks
    url_name = "reports:date_issues"
    title = "Date issues"
    intro = "Dates that are impossible inside a form, or that conflict with a date on another form of the same participant."
    empty = "No date issues here."

    def get(self, request, key=None):
        checks = visible_checks(request.user, self.builder)
        if not checks:
            raise PermissionDenied
        zones, sites, zone_id, site_id = _zone_site(request)

        counted = [(check, check_queryset(request.user, check, zone_id, site_id).count()) for check in checks]
        keys = {check.key for check in checks}
        if key not in keys:
            key = next((check.key for check, n in counted if n), checks[0].key)
        selected = next(check for check in checks if check.key == key)

        groups = defaultdict(list)
        for check, n in counted:
            groups[FORMS[check.form][0]].append((check, n))
        groups = [
            {"label": label, "total": sum(n for _, n in items), "checks": items}
            for label, items in groups.items()
        ]

        page = Paginator(check_queryset(request.user, selected, zone_id, site_id), self.paginate_by).get_page(request.GET.get("page"))
        rows = []
        for obj in page:
            screening = obj if obj.__class__.__name__ == "Screening" else obj.screening
            if selected.fields:  # future / too early: show the dates that are out of range
                dates = [
                    (re.sub(r"(\D)(\d)", r"\1 \2", name.replace("_", " ")).capitalize(), getattr(obj, name))
                    for name in selected.fields
                    if getattr(obj, name, None) and _out_of_range(selected, getattr(obj, name))
                ]
            else:
                dates = [(selected.a[1], resolve(obj, selected.a[0])), (selected.b[1], resolve(obj, selected.b[0]))]
            links = []
            forms = [selected.form, selected.b_form or selected.form]
            for form in dict.fromkeys(access.DIAGNOSIS if f == access.REGIMEN else f for f in forms):
                record = form_record(obj, form)
                if record is None:
                    continue
                edit_url, view_url = FORM_URLS[form]
                # EDCS/TBLIS records are read only: their page says where to fix them
                can_edit = form != access.EDCS_TBLIS and access.can_edit(request.user, form)
                regimen = form == access.DIAGNOSIS and access.REGIMEN in forms
                links.append({"label": "Diagnosis (regimen changes)" if regimen else FORMS[form][0],
                              "url_name": edit_url if can_edit else view_url, "pk": record.pk, "edit": can_edit,
                              "anchor": REGIMEN_ANCHOR if regimen else ""})
            rows.append({"obj": obj, "screening": screening, "dates": dates, "links": links})

        return render(request, self.template_name, {
            "groups": groups, "selected": selected, "selected_form_label": FORMS[selected.form][0],
            "page_obj": page, "rows": rows, "total": sum(n for _, n in counted),
            "zones": zones, "sites": sites, "selected_zone": zone_id, "selected_site": site_id,
            "filter_query": _filter_query(request),
            "url_name": self.url_name, "title": self.title, "intro": self.intro, "empty": self.empty,
            "is_dates": self.builder is None,
        })


class DsDrChecksView(DateIssuesView):
    """DS / DR answers that contradict each other on Enrollment, Clinic Lab, Zonal Lab and Diagnosis."""
    builder = staticmethod(dsdr_checks.build_checks)
    url_name = "reports:dsdr_checks"
    title = "DS / DR checks"
    intro = ("Drug-susceptible and drug-resistant answers that contradict each other: the previous episode on Enrollment, "
             "and the regimen prescribed on Diagnosis against the rifampicin results.")
    empty = "No DS / DR conflicts here."


def _out_of_range(check, value):
    return value > timezone.localdate() if check.key.endswith("_future") else value < STUDY_START


class OutcomeWithoutTreatmentView(LoginRequiredMixin, View):
    """Participants with a treatment outcome whose Diagnosis form does not say treatment started here."""
    template_name = "reports/data_quality/date_issues/outcome_without_treatment.html"
    paginate_by = 50

    @staticmethod
    def records(user):
        Screening = apps.get_model("nanopore", "Screening")
        # Treatment started: 1 Yes, 2 Referred elsewhere, 3 Not started. Anything but Yes with an outcome needs
        # following up: referred participants are listed so the site can confirm the outcome with the facility.
        qs = Screening.objects.filter(diagnosis__tb_outcome2__in=OUTCOMES).exclude(diagnosis__tb_treatment=1)
        return scope_queryset(user, qs, "site").annotate(substudy=substudy_case())

    def get(self, request):
        if not can_see_queries(request.user, access.DIAGNOSIS):
            raise PermissionDenied
        zones, sites, zone_id, site_id = _zone_site(request)
        qs = self.records(request.user)
        if zone_id:
            qs = qs.filter(site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(site_id=site_id)
        counts = {name: qs.filter(substudy=name).count() for name in SUBSTUDIES}
        substudy = request.GET.get("substudy")
        if substudy in SUBSTUDIES:
            qs = qs.filter(substudy=substudy)
        qs = qs.select_related(
            "site__district__region__zone", "diagnosis__tb_treatment", "diagnosis__tb_outcome2",
            "clinic_laboratory__xpert_mtb",
        ).order_by("site__district__region__zone__name", "site__name", "pid")
        page = Paginator(qs, self.paginate_by).get_page(request.GET.get("page"))
        return render(request, self.template_name, {
            "page_obj": page, "counts": counts, "total": sum(counts.values()), "selected_substudy": substudy or "",
            "zones": zones, "sites": sites, "selected_zone": zone_id, "selected_site": site_id,
            "filter_query": _filter_query(request),
        })
