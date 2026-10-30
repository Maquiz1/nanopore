from django import forms

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from nanopore.models import ZonalLaboratory


class CtrlIsolateForm(forms.ModelForm):
    """The number CTRL gives another zone's isolate; the DST then comes from the TBLIS upload by that number."""

    class Meta:
        model = ZonalLaboratory
        fields = ("isolate_unique_lab_no",)
        labels = {"isolate_unique_lab_no": ZONAL_LABELS["isolate_unique_lab_no"]}
        widgets = {"isolate_unique_lab_no": forms.TextInput(attrs={"class": "form-control"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Answered No/NA: the number stays optional, so a wrong one can be cleared here
        self.fields["isolate_unique_lab_no"].required = self.instance.culture_isolate_id == 1
