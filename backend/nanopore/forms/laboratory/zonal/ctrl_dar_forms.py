"""CTRL's forms for Dar es Salaam: what TBLIS can't supply, each saved on its own (nanopore/zonal_rules.py)."""
from django import forms
from nanopore.forms.reason_for_change import ReasonForChangeMixin

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from nanopore.forms.laboratory.nanopore_rules import _answered_yes, settle_nanopore
from nanopore.nanopore_runs import COPIED_FIELDS, final_answers, summarize
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

    def __init__(self, *args, runs=None, runs_changed=False, **kwargs):
        self.runs_changed = runs_changed  # a saved run changed or removed: needs a reason too
        super().__init__(*args, **kwargs)
        self.fields["nanopore_done"].required = True
        self.fields["nanopore_results"].queryset = NanoporeSequencingResults.objects.order_by("value")
        self.fields["sequencing_delayed_reasons"].queryset = NanoporeSequencingDelayedReasons.objects.order_by("value")
        if runs is None and self.instance.pk:
            runs = summarize(self.instance.nanopore_runs.all())
        self.runs = runs or summarize([])
        # 20(b)-21(h) are answered on each run; the final run's are copied here (read only).
        # A record sequenced before runs existed keeps what was typed until a run is added.
        self.legacy = bool(self.instance.pk and self.instance.nanopore_sequencing_date and not self.runs["count"])
        # Not shown on these pages (the runs carry them): locked, so saving keeps what is saved
        for name in COPIED_FIELDS:
            self.fields[name].disabled, self.fields[name].required = True, False
        self.fields["nanopore_sequencing_date"].help_text = "From the final run (the latest that didn't fail, else the latest)."

    def changed_answers(self):
        changed = super().changed_answers()
        return changed + ["nanopore runs"] if self.runs_changed else changed

    def clean(self):
        cleaned = super().clean()
        runs = self.runs
        if _answered_yes(cleaned, "nanopore_done"):
            if runs["count"]:
                cleaned.update(final_answers(runs))
                for name in COPIED_FIELDS:
                    self.errors.pop(name, None)
            else:
                # Every Yes has its run(s), older records too (their first run card is filled from their answers)
                self.add_error(None, "Add the run under Sequencing runs: 20(b) to 21(h), with its run number.")
        elif runs["count"]:
            self.add_error("nanopore_done", "Runs are recorded under Sequencing runs: answer Yes, or remove them.")
        settle_nanopore(self, cleaned, require=True)
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
