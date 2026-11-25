"""CTRL's forms for Dar es Salaam: what TBLIS can't supply, each saved on its own (nanopore/zonal_rules.py)."""
from django import forms
from nanopore.forms.reason_for_change import ReasonForChangeMixin

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from nanopore.forms.laboratory.nanopore_rules import _answered_yes, settle_nanopore
from nanopore.nanopore_runs import FAILED_RESULT_VALUE, summarize
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


class DarNanoporeForm(ReasonForChangeMixin, forms.ModelForm):
    """
    Section 7 / CTRL's Nanopore form. The runs (20(b), nanopore/nanopore_runs.py) give the final
    sequencing date, and "Failed" while no run has passed; 21 and 22 are answered for the passing run.
    runs: the runs as they will be saved ({"count", "first", "latest", "passed"}), None to read them.
    """
    Meta = type("Meta", (), _meta(NANOPORE_FIELDS))

    def __init__(self, *args, runs=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nanopore_done"].required = True
        self.fields["nanopore_results"].queryset = NanoporeSequencingResults.objects.order_by("value")
        self.fields["sequencing_delayed_reasons"].queryset = NanoporeSequencingDelayedReasons.objects.order_by("value")
        if runs is None and self.instance.pk:
            runs = summarize(self.instance.nanopore_runs.all())
        self.runs = runs or summarize([])
        # 20(b) comes from the runs now; a record sequenced before runs existed keeps its date
        date = self.fields["nanopore_sequencing_date"]
        date.disabled, date.required = True, False
        date.help_text = "From the runs: the date of the run that passed."

    def clean(self):
        cleaned = super().clean()
        runs = self.runs
        not_required = ()
        if _answered_yes(cleaned, "nanopore_done"):
            if runs["count"]:
                cleaned["nanopore_sequencing_date"] = runs["passed"] or runs["latest"]
                if runs["passed"] is None:
                    # Every run so far failed: waiting for a re-run, nothing analysed yet
                    cleaned["nanopore_results"] = NanoporeSequencingResults.objects.filter(value=FAILED_RESULT_VALUE).first()
                    not_required = ("epi_to_me",)
                elif getattr(cleaned.get("nanopore_results"), "value", None) == FAILED_RESULT_VALUE:
                    self.add_error("nanopore_results", "A run passed: choose its result.")
            elif not self.instance.nanopore_sequencing_date:
                self.add_error(None, "Add the run under 20(b): its date and whether it passed.")
        elif runs["count"]:
            self.add_error("nanopore_done", "Runs are recorded under 20(b): answer Yes, or remove them.")
        settle_nanopore(self, cleaned, require=True, not_required=not_required)
        return cleaned

    has_answers = True


class DarLpaForm(ReasonForChangeMixin, forms.ModelForm):
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

    @property
    def has_answers(self):
        return any(name != "reason_for_change" for name in self.fields)
