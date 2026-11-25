"""The Zonal Lab form's sections (nanopore/zonal_sections.py), each saved on its own."""
from django import forms

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.forms.reason_for_change import ReasonForChangeMixin
from nanopore.models import ZonalLaboratory
from nanopore.zonal_rules import is_lab_number_only
from nanopore.zonal_sections import BY_KEY, DAR_FIELDS
from options.models import SampleAppearance


def _meta(names):
    return type("Meta", (), {
        "model": ZonalLaboratory,
        "fields": names,
        "labels": {name: ZONAL_LABELS[name] for name in names if name in ZONAL_LABELS},
        "widgets": {name: ZonalLaboratoryForm.Meta.widgets[name] for name in names if name in ZonalLaboratoryForm.Meta.widgets},
    })


class ReceptionForm(ReasonForChangeMixin, forms.ModelForm):
    """1. Sample reception. Dar es Salaam takes only the lab number: TB-LIS gives the rest."""
    section = BY_KEY["reception"]
    Meta = _meta(BY_KEY["reception"].fields)

    def __init__(self, *args, screening=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.dar = is_lab_number_only(screening)
        if self.dar:
            for name in self.section.fields:
                if name not in DAR_FIELDS["reception"]:
                    del self.fields[name]
        else:
            self.fields["appearance"].queryset = SampleAppearance.objects.order_by("value")
        for name in self.section.fields:
            if name in self.fields:
                self.fields[name].required = True

    has_answers = True
