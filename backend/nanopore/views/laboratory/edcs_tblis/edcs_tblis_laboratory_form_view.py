from django.shortcuts import get_object_or_404, render
from django.views import View

from nanopore.forms.laboratory.edcs_tblis.edcs_tblis_lab_form import EdcsTblisZonalForm
from nanopore.models import EdcsTblisZonal
from nanopore.tblis_status import record_statuses
from nanopore.zonal_rules import is_lab_number_only, viewable_edcs_records
from utils import access
from utils.access_mixins import FormAccessMixin


class EdcsTblisFormView(FormAccessMixin, View):
    """
    An EDCS/TBLIS record, read only: the daily sync rebuilds it from the Zonal Lab
    form and the TBLIS upload, so fixes are made on those.
    """
    http_method_names = ["get", "head", "options"]
    access_form = access.EDCS_TBLIS
    template_name = "nanopore/laboratory/edcs_tblis/edcs_tblis_laboratory_form.html"

    def has_form_access(self, request, kwargs):
        # CTRL reads every zone's record from its own forms
        return super().has_form_access(request, kwargs) or access.is_ctrl_lab(request.user)

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(viewable_edcs_records(request.user), pk=kwargs["pk"])
        form = EdcsTblisZonalForm(instance=obj, screening_instance=obj.screening)
        for field in form.fields.values():
            field.disabled = True
        return render(request, self.template_name, {
            "form": form, "object": obj, "screening": obj.screening,
            "zonal_lab": getattr(obj.screening, "zonal_laboratory", None),
            "dst_without_isolate": is_lab_number_only(obj.screening),
            "tblis": record_statuses(EdcsTblisZonal.objects.filter(pk=obj.pk)).get(obj.screening_id),
        })
