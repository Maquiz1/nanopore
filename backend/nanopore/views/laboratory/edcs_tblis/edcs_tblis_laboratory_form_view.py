from django.shortcuts import get_object_or_404, render
from django.views import View

from nanopore.forms.laboratory.edcs_tblis.edcs_tblis_lab_form import EdcsTblisZonalForm
from nanopore.models import EdcsTblisZonal
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

    def get(self, request, *args, **kwargs):
        obj = get_object_or_404(self.scope(EdcsTblisZonal.objects.all()), pk=kwargs["pk"])
        form = EdcsTblisZonalForm(instance=obj, screening_instance=obj.screening)
        for field in form.fields.values():
            field.disabled = True
        return render(request, self.template_name, {
            "form": form, "object": obj, "screening": obj.screening,
            "zonal_lab": getattr(obj.screening, "zonal_laboratory", None),
        })
