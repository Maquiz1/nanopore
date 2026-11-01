from django.utils.http import urlencode
from django.views.generic import ListView

from nanopore.models import ZonalLaboratory
from nanopore.models.discrepancies import TblisFollowUp
from nanopore.tblis_file import FILTER_REASONS, FOLLOW_UP_REASONS
from utils import access
from utils.access_mixins import FeatureAccessMixin


class TblisFollowUpView(FeatureAccessMixin, ListView):
    """Latest TB-LIS upload: rows left out because the specimen or GeneXpert wasn't recorded."""
    access_feature = access.TBLIS_FOLLOW_UP
    template_name = "nanopore/laboratory/edcs_tblis/tblis_follow_up.html"
    context_object_name = "rows"
    paginate_by = 50

    def param(self, key):
        return self.request.GET.get(key, "").strip()

    def get_queryset(self):
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
