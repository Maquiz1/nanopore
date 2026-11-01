"""CTRL's forms for Dar es Salaam: what TBLIS can't supply, each saved on its own (nanopore/zonal_rules.py)."""
from django import forms

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from nanopore.forms.laboratory.nanopore_rules import settle_nanopore
from nanopore.forms.laboratory.zonal.zonallabform import ZonalLaboratoryForm
from nanopore.models import ZonalLaboratory
from nanopore.zonal_rules import NANOPORE_PREFIXES, lpa_lines_done
from options.models import NanoporeSequencingDelayedReasons, NanoporeSequencingResults

NANOPORE_FIELDS = tuple(f for f in ZonalLaboratoryForm.Meta.fields if f.startswith(NANOPORE_PREFIXES))


def _meta(names):
    return {
        "model": ZonalLaboratory,
        "fields": names,
        "labels": {name: ZONAL_LABELS[name] for name in names if name in ZONAL_LABELS},
        "widgets": {name: ZonalLaboratoryForm.Meta.widgets[name] for name in names if name in ZonalLaboratoryForm.Meta.widgets},
    }


class DarNanoporeForm(forms.ModelForm):
    Meta = type("Meta", (), _meta(NANOPORE_FIELDS))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nanopore_done"].required = True
        self.fields["nanopore_results"].queryset = NanoporeSequencingResults.objects.order_by("value")
        self.fields["sequencing_delayed_reasons"].queryset = NanoporeSequencingDelayedReasons.objects.order_by("value")

    def clean(self):
        cleaned = super().clean()
        settle_nanopore(self, cleaned, require=True)
        return cleaned


class DarLpaForm(forms.ModelForm):
    """Only the checkboxes of the LPA lines TBLIS says were done; both are required then."""
    Meta = type("Meta", (), _meta(("first_line_drugs", "second_line_drugs")))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lpa1_done, self.lpa2_done = lpa_lines_done(self.instance.screening)
        for name, done in (("first_line_drugs", self.lpa1_done), ("second_line_drugs", self.lpa2_done)):
            if done:
                self.fields[name].required = True
            else:
                del self.fields[name]
