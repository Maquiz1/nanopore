# nanopore/views/status.py
from nanopore.substudy import OUTCOMES, SUBSTUDY_2, SUBSTUDY_KEYS, substudy_case, substudy_q
from django.views.generic import ListView
from nanopore.models import Screening
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context
from utils import access
from utils.access import assigned_locations
from utils.access_mixins import AnyFormAccessMixin
from django.db.models import Count, Q
from django.utils.http import urlencode

# ?list_type= tabs: key -> (tab label, page title, what the list holds)
LIST_TYPES = {
    "screened": ("All screened", "Participants", "Everyone screened, with the status of each form."),
    "eligible": ("Eligible", "Eligible participants", "Screened participants who meet every inclusion and exclusion criterion."),
    "enrolled": ("Enrolled", "Enrolled participants", "Participants with an Enrollment form."),
    "completed": ("Completed", "Completed participants", "Substudy 2 participants with a treatment outcome recorded."),
}
LIST_TYPE_Q = {
    "screened": Q(),
    "eligible": Q(eligible=True),
    "enrolled": Q(enrollment__isnull=False),
    # Completed = Substudy 2 enrolled with a treatment outcome (nanopore/substudy.py)
    "completed": substudy_q(SUBSTUDY_2) & Q(enrollment__isnull=False, diagnosis__tb_outcome2__in=OUTCOMES),
}
FILTER_KEYS = ("zone", "site", "pid", "unique_lab_no", "start_date", "end_date", "status", "substudy")


class FormStatusListView(AnyFormAccessMixin, ListView):
    access_forms = access.ALL_FORMS
    model = Screening
    template_name = "nanopore/form_status/form_status_list.html"
    context_object_name = "screenings"
    paginate_by = 25

    def get_list_type(self):
        list_type = self.request.GET.get("list_type", "screened")
        return list_type if list_type in LIST_TYPES else "screened"

    def filtered_queryset(self):
        """Role scope + the filter bar, before the list-type tab."""
        qs = Screening.objects.select_related(
            "enrollment",
            "clinic_laboratory",
            "clinic_laboratory__xpert_mtb",
            "zonal_laboratory",
            "diagnosis",
            "enrolled",
            "site",
            "site__district__region__zone",
        )
        qs = filter_queryset_by_user_role(self.request.user, qs)

        get = self.request.GET.get
        if get("zone"):
            qs = qs.filter(site__district__region__zone_id=get("zone"))
        if get("site"):
            qs = qs.filter(site_id=get("site"))
        if get("pid"):
            qs = qs.filter(pid__icontains=get("pid").strip())
        if get("unique_lab_no"):
            qs = qs.filter(zonal_laboratory__unique_lab_no__icontains=get("unique_lab_no").strip())
        # Either date works on its own
        if get("start_date"):
            qs = qs.filter(screening_date__gte=get("start_date"))
        if get("end_date"):
            qs = qs.filter(screening_date__lte=get("end_date"))
        if get("status") == "eligible":
            qs = qs.filter(eligible=True)
        elif get("status") == "not_eligible":
            qs = qs.filter(eligible=False)
        if get("substudy") in SUBSTUDY_KEYS:
            qs = qs.filter(substudy_q(SUBSTUDY_KEYS[get("substudy")]))
        return qs

    def get_queryset(self):
        self.base_qs = self.filtered_queryset()
        qs = self.base_qs.filter(LIST_TYPE_Q[self.get_list_type()])
        # Substudy of each row (one definition: nanopore/substudy.py)
        return qs.annotate(substudy_case=substudy_case()).order_by("-screening_date", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_role_context(self.request.user))

        assigned_zones, assigned_sites = assigned_locations(self.request.user)
        context.update({"assigned_zones": assigned_zones, "assigned_sites": assigned_sites})

        list_type = self.get_list_type()
        counts = self.base_qs.aggregate(**{
            key: Count("pk", filter=q, distinct=True) if q else Count("pk", distinct=True)
            for key, q in LIST_TYPE_Q.items()
        })
        context["tabs"] = [
            {"key": key, "label": label, "count": counts[key], "active": key == list_type}
            for key, (label, _, _) in LIST_TYPES.items()
        ]
        context["list_type"] = list_type
        context["page_title"], context["page_note"] = LIST_TYPES[list_type][1:]

        # Keep the filter values in the form and in the pager / tab links
        selected = {key: self.request.GET.get(key, "").strip() for key in FILTER_KEYS}
        for key, value in selected.items():
            context[f"selected_{key}"] = value
        filters = {key: value for key, value in selected.items() if value}
        context["filters_active"] = bool(filters)
        context["filter_params"] = urlencode(filters)
        context["query_params"] = urlencode({**filters, "list_type": list_type})
        context["show_location_filter"] = context["sites"].count() > 1 if hasattr(context["sites"], "count") else len(context["sites"]) > 1
        return context
