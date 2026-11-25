"""
Nanopore sequencing runs (Zonal Lab section 7, question 20(b)): every attempt is kept, and the
Zonal Lab's own Nanopore answers stay the final result.

  * Each run: its date, Passed or Failed (with the reason), and an optional run / flow cell ID.
    Runs are numbered 1, 2, 3... by date; nobody types the number.
  * The final sequencing date (20(b) on exports) is the latest passing run's date.
  * While every run so far has failed, the final result is "Failed" (waiting for a re-run), and
    the EPI2ME questions aren't asked yet; once a run passes, 21 and 22 are answered for it.
  * Records sequenced before runs existed keep their date until a run is added (start from now).
"""
from django import forms
from django.forms import inlineformset_factory

from nanopore.models import NanoporeRun, ZonalLaboratory
from nanopore.models.nanopore_run import FAILED, PASSED

FAILED_RESULT_VALUE = 4  # NanoporeSequencingResults "Failed"


class RunForm(forms.ModelForm):
    class Meta:
        model = NanoporeRun
        fields = ("run_date", "run_number", "outcome", "failure_reason", "failure_other", "run_id")
        labels = {"run_date": "Date of run", "run_number": "Run number (NN/YY)", "outcome": "Outcome", "failure_reason": "Why it failed",
                  "failure_other": "Other reason", "run_id": "Run ID / flow cell ID (optional)"}
        widgets = {
            "run_date": forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"}),
            "run_number": forms.TextInput(attrs={"class": "form-control form-control-sm run-number", "placeholder": "NN/YY",
                                                 "inputmode": "numeric", "maxlength": "5", "autocomplete": "off"}),
            "outcome": forms.Select(attrs={"class": "form-select form-select-sm run-outcome"}),
            "failure_reason": forms.Select(attrs={"class": "form-select form-select-sm run-reason"}),
            "failure_other": forms.TextInput(attrs={"class": "form-control form-control-sm run-other"}),
            "run_id": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        }

    def clean_run_number(self):
        value = (self.cleaned_data.get("run_number") or "").strip()
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) == 4 and "/" not in value:  # typed without the slash
            value = f"{digits[:2]}/{digits[2:]}"
        return value

    def clean(self):
        cleaned = super().clean()
        number, day = cleaned.get("run_number"), cleaned.get("run_date")
        if number and day and "/" in number and number.split("/")[1] != f"{day:%y}":
            self.add_error("run_number", f"The year in the run number ({number.split('/')[1]}) doesn't match the run date ({day:%Y}).")
        if cleaned.get("outcome") == PASSED:
            cleaned["failure_reason"], cleaned["failure_other"] = "", ""
        elif cleaned.get("outcome") == FAILED:
            if not cleaned.get("failure_reason"):
                self.add_error("failure_reason", "Required when the run failed.")
            elif cleaned.get("failure_reason") != "other":
                cleaned["failure_other"] = ""
            elif not cleaned.get("failure_other"):
                self.add_error("failure_other", "Required when the reason is Other.")
        return cleaned


RunFormSet = inlineformset_factory(ZonalLaboratory, NanoporeRun, form=RunForm, extra=0, can_delete=True)
FirstRunFormSet = inlineformset_factory(ZonalLaboratory, NanoporeRun, form=RunForm, extra=1, can_delete=True)


def runs_formset(record, data=None, read_only=False):
    """The runs of a Zonal Lab record; one empty row to start with when there are none yet."""
    has_runs = record.pk is not None and record.nanopore_runs.exists()
    formset = (RunFormSet if has_runs or read_only else FirstRunFormSet)(data, instance=record, prefix="runs")
    if read_only:
        for form in formset.forms:
            for field in form.fields.values():
                field.disabled = True
    return formset


def summarize(runs):
    """{"count", "first", "latest", "passed"} of runs: (date, outcome) pairs or NanoporeRun objects."""
    pairs = sorted((r.run_date, r.outcome) if hasattr(r, "run_date") else r for r in runs)
    passed = [d for d, outcome in pairs if outcome == PASSED]
    return {"count": len(pairs), "first": pairs[0][0] if pairs else None, "latest": pairs[-1][0] if pairs else None,
            "passed": passed[-1] if passed else None}


def summary_from_formset(formset):
    """The runs as they will be after saving the (valid) formset."""
    runs = []
    for form in formset.forms:
        data = getattr(form, "cleaned_data", None) or {}
        if not data or data.get("DELETE") or not data.get("run_date") or not data.get("outcome"):
            continue
        runs.append((data["run_date"], data["outcome"]))
    return summarize(runs)


def save_runs(formset, record, user):
    formset.instance = record
    for run in formset.save(commit=False):
        run.updated_by = user
        if run.pk is None:
            run.created_by = user
        run.save()
    for run in formset.deleted_objects:
        run.delete()


def export_columns(record):
    """Per-participant export columns: number of runs, first and final run dates."""
    if record is None:
        return ["", "", ""]
    summary = summarize(record.nanopore_runs.all())
    return [summary["count"] or "", summary["first"] or "", summary["passed"] or summary["latest"] or ""]


EXPORT_HEADER = ["nanopore_runs", "nanopore_first_run_date", "nanopore_final_run_date"]
