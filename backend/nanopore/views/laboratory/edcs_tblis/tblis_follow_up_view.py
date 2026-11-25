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


# ── Accepted items (reports/services/accepted.py): "followed up, nothing to change in TB-LIS" ──
def row_values(row):
    """A not-recorded TB-LIS row, kept by its lab number so the acceptance survives the next upload."""
    return {"reason": row.reason, "specimen": row.specimen, "genexpert": row.genexpert}


def lab_values(found):
    return {"state": found.state}


def _visible_labs(user):
    labs = ZonalLaboratory.objects.all()
    if not (getattr(user, "is_superuser", False) or access.is_unscoped(user) or access.is_ctrl_lab(user)):
        labs = access.scope_queryset(user, labs, "screening__site")
    return labs


def accepted_rows(rows):
    """{labno: AcceptedCheck} of not-recorded rows whose acceptance holds."""
    from reports.services.accepted import TBLIS_FOLLOW_UP, holding
    return holding(TBLIS_FOLLOW_UP, NOT_RECORDED, rows, row_values, key=lambda row: row.labno)


def accepted_labs(list_key, labs, found):
    """{lab pk: AcceptedCheck} of rejected / not-in-latest records whose acceptance holds."""
    from reports.services.accepted import TBLIS_FOLLOW_UP, holding
    return holding(TBLIS_FOLLOW_UP, list_key, labs, lambda lab: lab_values(found[lab.screening_id]))


def follow_up_item(user, check_key, object_id):
    from reports.services.accepted_lists import Item
    if not access.has_feature(user, access.TBLIS_FOLLOW_UP):
        return None
    if check_key == NOT_RECORDED:
        row = TblisFollowUp.objects.filter(labno=object_id).first()
        if row is None:
            return None
        lab = ZonalLaboratory.objects.filter(unique_lab_no=row.labno).select_related("screening").first()
        return Item(row, row_values(row), lab.screening if lab else None, lab)
    if check_key in RECORD_LISTS and str(object_id).isdigit():
        lab = _visible_labs(user).filter(pk=object_id).select_related("screening").first()
        if lab is None:
            return None
        found = tblis_status.record_statuses(ZonalLaboratory.objects.filter(pk=lab.pk)).get(lab.screening_id)
        if found is None or found.state != RECORD_LISTS[check_key]:
            return None
        return Item(lab, lab_values(found), lab.screening, lab)
    return None


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

    def show_accepted(self):
        return self.param("show") == "accepted"

    def study_records(self, state):
        labs = _visible_labs(self.request.user)
        found = tblis_status.record_statuses(labs)
        labs = labs.filter(screening_id__in=[pk for pk, one in found.items() if one.state == state])
        kept = accepted_labs(self.selected_list(), labs, found)
        self.accepted_total = len(kept)
        ids = [int(pk) for pk in kept]
        labs = labs.filter(pk__in=ids) if self.show_accepted() else labs.exclude(pk__in=ids)
        if self.param("q"):
            q = self.param("q")
            labs = labs.filter(Q(screening__pid__icontains=q) | Q(unique_lab_no__icontains=q) | Q(isolate_unique_lab_no__icontains=q))
        dar = set(labs.filter(ctrl_q()).values_list("pk", flat=True))
        return [
            {"lab": lab, "found": found[lab.screening_id], "accepted": kept.get(str(lab.pk)), "oid": lab.pk,
             "number": lab.unique_lab_no if lab.pk in dar else lab.isolate_unique_lab_no,
             "kind": "Sputum" if lab.pk in dar else "Isolate"}
            for lab in labs.select_related("screening__site").order_by("screening__site__name", "screening__pid")
        ]

    def get_queryset(self):
        if self.selected_list() in RECORD_LISTS:
            return self.study_records(RECORD_LISTS[self.selected_list()])
        qs = TblisFollowUp.objects.all()
        from reports.services.accepted import TBLIS_FOLLOW_UP, _active
        wanted = list(_active(TBLIS_FOLLOW_UP).get(NOT_RECORDED, {}))
        kept = accepted_rows(TblisFollowUp.objects.filter(labno__in=wanted)) if wanted else {}
        self.accepted_total = len(kept)
        qs = qs.filter(labno__in=list(kept)) if self.show_accepted() else qs.exclude(labno__in=list(kept))
        self.kept = kept
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
        context.update({"lists": LISTS, "shown": shown, "show_accepted": self.show_accepted(),
                        "accepted_total": getattr(self, "accepted_total", 0)})
        if shown in RECORD_LISTS:
            selected = {"q": self.param("q")}
            context["accept_base"] = urlencode({k: v for k, v in {**selected, "list": shown}.items() if v})
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
            row.accepted = self.kept.get(row.labno)
        selected = {key: self.param(key) for key in ("q", "reason", "region")}
        context["accept_base"] = urlencode({k: v for k, v in {**selected, "list": shown}.items() if v})
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
