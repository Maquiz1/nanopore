from django import forms
from nanopore.forms.reason_for_change import ReasonForChangeMixin

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from nanopore.models import ZonalLaboratory
from options.models import YesNoNA


YES = 1


class CtrlIsolateForm(ReasonForChangeMixin, forms.ModelForm):
    """
    Question 11 for another zone's form (CTRL or the site may answer it), and the number CTRL
    gives the isolate; the DST then comes from the TBLIS upload by that number.
    """
    FIELDS = ("culture_isolate", "isolate_date", "isolate_unique_lab_no")

    class Meta:
        model = ZonalLaboratory
        fields = ("culture_isolate", "isolate_date", "isolate_unique_lab_no")
        labels = {name: ZONAL_LABELS[name] for name in ("culture_isolate", "isolate_date", "isolate_unique_lab_no")}
        widgets = {
            "culture_isolate": forms.Select(attrs={"class": "form-select"}),
            "isolate_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "isolate_unique_lab_no": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        answer = cleaned.get("culture_isolate")
        if answer is None and cleaned.get("isolate_unique_lab_no"):
            # A CTRL isolate number means the isolate was submitted
            answer = cleaned["culture_isolate"] = YesNoNA.objects.filter(pk=YES).first()
        if answer and answer.pk == YES:
            if not cleaned.get("isolate_unique_lab_no"):
                self.add_error("isolate_unique_lab_no", "Required when the isolate was submitted to CTRL.")
        else:  # No, Na or not answered: no isolate, so no date or number (a wrong number is cleared here)
            cleaned["isolate_date"] = None
            cleaned["isolate_unique_lab_no"] = None
        return cleaned
