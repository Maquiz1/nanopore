from django.db.models import Q
from django.utils.http import urlencode
from django.views.generic import ListView

from nanopore import tblis_status
from nanopore.edcs_tblis_cards import ctrl_q
from nanopore.models import ZonalLaboratory
from nanopore.models.discrepancies import TblisFollowUp
from nanopore.tblis_file import FILTER_REASONS, FOLLOW_UP_REASONS
from utils import access
from utils.access_mixins import FeatureAccessMixin

NOT_RECORDED, REJECTED, ABSENT = "not-recorded", "rejected", "absent"
RECORD_LISTS = {REJECTED: tblis_status.REJECTED, ABSENT: tblis_status.NOT_IN_LATEST}
LISTS = ((NOT_RECORDED, "Not recorded in TB-LIS"), (REJECTED, "Rejected: results not used"), (ABSENT, "Not in latest file"))


class TblisFollowUpView(FeatureAccessMixin, ListView):
    """
    For CTRL to follow up: the latest upload's rows with no specimen or GeneXpert recorded,
    and the study records TB-LIS rejects or no longer has in its latest file (nanopore/tblis_status.py).
    """
    access_feature = access.TBLIS_FOLLOW_UP
    template_name = "nanopore/laboratory/edcs_tblis/tblis_follow_up.html"
    context_object_name = "rows"
    paginate_by = 50

    def param(self, key):
        return self.request.GET.get(key, "").strip()

    def selected_list(self):
        return self.param("list") if self.param("list") in RECORD_LISTS else NOT_RECORDED

    def study_records(self, state):
        user = self.request.user
        labs = ZonalLaboratory.objects.all()
        if not access.is_unscoped(user) and not access.is_ctrl_lab(user):
            labs = access.scope_queryset(user, labs, "screening__site")
        found = tblis_status.record_statuses(labs)
        labs = labs.filter(screening_id__in=[pk for pk, one in found.items() if one.state == state])
        if self.param("q"):
            q = self.param("q")
            labs = labs.filter(Q(screening__pid__icontains=q) | Q(unique_lab_no__icontains=q) | Q(isolate_unique_lab_no__icontains=q))
        dar = set(labs.filter(ctrl_q()).values_list("pk", flat=True))
        return [
            {"lab": lab, "found": found[lab.screening_id],
             "number": lab.unique_lab_no if lab.pk in dar else lab.isolate_unique_lab_no,
             "kind": "Sputum" if lab.pk in dar else "Isolate"}
            for lab in labs.select_related("screening__site").order_by("screening__site__name", "screening__pid")
        ]

    def get_queryset(self):
        if self.selected_list() in RECORD_LISTS:
            return self.study_records(RECORD_LISTS[self.selected_list()])
        qs = TblisFollowUp.objects.all()
        if self.param("reason") in FOLLOW_UP_REASONS:
            qs = qs.filter(reason=self.param("reason"))
        if self.param("q"):
            qs = qs.filter(labno__icontains=self.param("q"))
        if self.param("region"):
            qs = qs.filter(region=self.param("region"))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shown = self.selected_list()
        context.update({"lists": LISTS, "shown": shown})
        if shown in RECORD_LISTS:
            selected = {"q": self.param("q")}
            context.update({
                "selected": selected, "filters_active": bool(selected["q"]), "total": 0,
                "query_params": urlencode({k: v for k, v in {**selected, "list": shown}.items() if v}),
            })
            return context
        rows = list(context["rows"])
        labs = ZonalLaboratory.objects.filter(unique_lab_no__in=[row.labno for row in rows]).select_related("screening__site")
        by_labno = {lab.unique_lab_no: lab.screening for lab in labs}
        for row in rows:
            row.screening = by_labno.get(row.labno)
            row.reason_label = FILTER_REASONS[row.reason]
        selected = {key: self.param(key) for key in ("q", "reason", "region")}
        context.update({
            "rows": rows,
            "total": TblisFollowUp.objects.count(),
            "reasons": [(key, FILTER_REASONS[key]) for key in FOLLOW_UP_REASONS],
            "regions": TblisFollowUp.objects.exclude(region="").order_by("region").values_list("region", flat=True).distinct(),
            "selected": selected,
            "filters_active": any(selected.values()),
            "query_params": urlencode({k: v for k, v in selected.items() if v}),
        })
        return context
