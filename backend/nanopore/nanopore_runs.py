"""
Nanopore sequencing runs (Zonal Lab section 7): a sample can be sequenced several times; every
run is kept, with its own answers to 20(b)-21(h). The Zonal Lab's own answers stay the final result.

  * Each run: 20(b) its date, the lab's run number (NN/YY), an optional run / flow cell ID,
    21(a)-(d) its EPI2ME analysis, 21(e) its result (Failed means the run failed, with the reason),
    and 21(f)-(h) any delay. Attempts are numbered 1, 2, 3... by date; nobody types the number.
  * The final run is the latest one that didn't fail, else the latest: its 20(b)-21(h) are copied
    to the Zonal Lab's own answers (read only there), which exports, queries and the merge use.
    22 (drug results) is answered once, for the final run, when its result is MTBC.
  * Records sequenced before runs existed keep what was typed until a run is added (from 25 Nov 2026).
"""
from django import forms
from django.forms import inlineformset_factory

from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS
from nanopore.models import NanoporeRun, ZonalLaboratory
from nanopore.models.nanopore_run import FAILED, PASSED
from options.models import NanoporeSequencingDelayedReasons, NanoporeSequencingResults

FAILED_RESULT_VALUE = 4  # NanoporeSequencingResults "Failed"
YES = 1                  # YesNo
OTHER_REASON = 96        # delay reason "Other, specify"
EPI2ME_FIELDS = ("epi_to_me", "epi_to_me_date", "epi_to_me_version", "sequencing_results")
DELAY_FIELDS = ("sequencing_delayed", "sequencing_delayed_days", "sequencing_delayed_reasons", "sequencing_delayed_others")
# The Zonal Lab answers a run gives (the final run's are copied there)
COPIED_FIELDS = ("nanopore_sequencing_date", *EPI2ME_FIELDS, "nanopore_results", *DELAY_FIELDS)


def _label(name, fallback):
    return ZONAL_LABELS.get(name, fallback)


class RunForm(forms.ModelForm):
    class Meta:
        model = NanoporeRun
        fields = ("run_date", "run_number", "run_id", *EPI2ME_FIELDS, "nanopore_results",
                  "failure_reason", "failure_other", *DELAY_FIELDS)
        labels = {
            "run_date": _label("nanopore_sequencing_date", "20(b). Date of Nanopore sequencing conducted"),
            "run_number": "Run number (NN/YY)", "run_id": "Run ID / flow cell ID (optional)",
            "failure_reason": "Why the run failed", "failure_other": "Other reason",
            **{name: _label(name, name) for name in (*EPI2ME_FIELDS, "nanopore_results", *DELAY_FIELDS)},
        }
        widgets = {
            "run_date": forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"}),
            "run_number": forms.TextInput(attrs={"class": "form-control form-control-sm run-number", "placeholder": "NN/YY",
                                                 "inputmode": "numeric", "maxlength": "5", "autocomplete": "off"}),
            "run_id": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "epi_to_me": forms.Select(attrs={"class": "form-select form-select-sm run-epi"}),
            "epi_to_me_date": forms.DateInput(attrs={"type": "date", "class": "form-control form-control-sm"}),
            "epi_to_me_version": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "sequencing_results": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "nanopore_results": forms.Select(attrs={"class": "form-select form-select-sm run-result"}),
            "failure_reason": forms.Select(attrs={"class": "form-select form-select-sm run-reason"}),
            "failure_other": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "sequencing_delayed": forms.Select(attrs={"class": "form-select form-select-sm run-delayed"}),
            "sequencing_delayed_days": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": "0"}),
            "sequencing_delayed_reasons": forms.CheckboxSelectMultiple(attrs={"class": "run-delay-reason"}),
            "sequencing_delayed_others": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nanopore_results"].queryset = NanoporeSequencingResults.objects.order_by("value")
        self.fields["sequencing_delayed_reasons"].queryset = NanoporeSequencingDelayedReasons.objects.order_by("value")
        # Asked on every run (the rest follow from these answers)
        for name in ("run_date", "run_number", "epi_to_me", "nanopore_results", "sequencing_delayed"):
            self.fields[name].required = True

    def clean_run_number(self):
        value = (self.cleaned_data.get("run_number") or "").strip()
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) == 4 and "/" not in value:  # typed without the slash
            value = f"{digits[:2]}/{digits[2:]}"
        return value

    def _require(self, cleaned, names, message="Required."):
        for name in names:
            value = cleaned.get(name)
            if (value in (None, "") or (hasattr(value, "exists") and not value.exists())) and name not in self.errors:
                self.add_error(name, message)

    def _clear(self, cleaned, names):
        for name in names:
            field = self.fields[name]
            cleaned[name] = field.queryset.none() if isinstance(field, forms.ModelMultipleChoiceField) else (
                "" if isinstance(field, forms.CharField) else None)

    def clean(self):
        cleaned = super().clean()
        number, day = cleaned.get("run_number"), cleaned.get("run_date")
        if number and day and "/" in number and number.split("/")[1] != f"{day:%y}":
            self.add_error("run_number", f"The year in the run number ({number.split('/')[1]}) doesn't match the run date ({day:%Y}).")
        # 21(a)-(d): EPI2ME used? Yes opens its date, version and .csv export
        self._require(cleaned, ("epi_to_me",))
        if getattr(cleaned.get("epi_to_me"), "pk", None) == YES:
            self._require(cleaned, EPI2ME_FIELDS[1:], "Required when EPI2ME was used.")
        else:
            self._clear(cleaned, EPI2ME_FIELDS[1:])
        # 21(e): the result; Failed means the run failed, and why
        self._require(cleaned, ("nanopore_results",))
        if getattr(cleaned.get("nanopore_results"), "value", None) == FAILED_RESULT_VALUE:
            self._require(cleaned, ("failure_reason",), "Required when the run failed.")
            if cleaned.get("failure_reason") == "other":
                self._require(cleaned, ("failure_other",), "Required when the reason is Other.")
            else:
                cleaned["failure_other"] = ""
        else:
            cleaned["failure_reason"], cleaned["failure_other"] = "", ""
        # 21(f)-(h): a delay, its days and reasons
        self._require(cleaned, ("sequencing_delayed",))
        if getattr(cleaned.get("sequencing_delayed"), "pk", None) == YES:
            self._require(cleaned, ("sequencing_delayed_days", "sequencing_delayed_reasons"), "Required when there was a delay.")
            reasons = cleaned.get("sequencing_delayed_reasons")
            if reasons is not None and reasons.filter(value=OTHER_REASON).exists():
                self._require(cleaned, ("sequencing_delayed_others",), "Required when the reason is Other.")
            else:
                cleaned["sequencing_delayed_others"] = ""
        else:
            self._clear(cleaned, DELAY_FIELDS[1:])
        return cleaned


RunFormSet = inlineformset_factory(ZonalLaboratory, NanoporeRun, form=RunForm, extra=0, can_delete=True)
FirstRunFormSet = inlineformset_factory(ZonalLaboratory, NanoporeRun, form=RunForm, extra=1, can_delete=True)


def legacy_run(record):
    """A record sequenced before runs existed: its saved answers, as the first run card's starting values."""
    if record.pk is None or not record.nanopore_sequencing_date:
        return None
    values = {"run_date": record.nanopore_sequencing_date}
    for name in (*EPI2ME_FIELDS, "nanopore_results", *DELAY_FIELDS):
        value = getattr(record, name)
        if name == "sequencing_delayed_reasons":
            value = list(value.all().values_list("pk", flat=True))
        elif hasattr(value, "pk"):
            value = value.pk
        values[name] = value
    return values


def runs_formset(record, data=None, read_only=False):
    """The runs of a Zonal Lab record; one run to start with when there are none yet (filled with an
    older record's answers, so only the run number is left to add)."""
    has_runs = record.pk is not None and record.nanopore_runs.exists()
    factory = RunFormSet if has_runs or read_only else FirstRunFormSet
    start = None if has_runs else legacy_run(record)
    formset = factory(data, instance=record, prefix="runs", initial=[start] if start else None)
    if read_only:
        for form in formset.forms:
            for field in form.fields.values():
                field.disabled = True
    return formset


def _failed(result):
    return getattr(result, "value", None) == FAILED_RESULT_VALUE


def _as_dict(run):
    """A run's answers, from a saved NanoporeRun or a dict built from a valid run form."""
    if isinstance(run, dict):
        return run
    answers = {name: getattr(run, name) for name in (*EPI2ME_FIELDS, "nanopore_results", *DELAY_FIELDS)
               if name != "sequencing_delayed_reasons"}
    answers["sequencing_delayed_reasons"] = list(run.sequencing_delayed_reasons.all()) if run.pk else []
    return {"run_date": run.run_date, **answers}


def summarize(runs):
    """{"count", "first", "latest", "passed", "final"}; final: the answers of the latest run that
    didn't fail, else of the latest run (None without runs)."""
    rows = sorted((_as_dict(r) for r in runs), key=lambda r: r["run_date"])
    passed = [r for r in rows if not _failed(r.get("nanopore_results"))]
    final = passed[-1] if passed else (rows[-1] if rows else None)
    return {"count": len(rows), "first": rows[0]["run_date"] if rows else None, "latest": rows[-1]["run_date"] if rows else None,
            "passed": passed[-1]["run_date"] if passed else None, "final": final}


def summary_from_formset(formset):
    """The runs as they will be after saving the (valid) formset."""
    runs = []
    for form in formset.forms:
        data = getattr(form, "cleaned_data", None) or {}
        if not data or data.get("DELETE") or not data.get("run_date"):
            continue
        runs.append({"run_date": data["run_date"],
                     **{name: data.get(name) for name in (*EPI2ME_FIELDS, "nanopore_results", *DELAY_FIELDS)}})
    return summarize(runs)


def final_answers(summary):
    """The Zonal Lab answers the final run gives (field name -> value)."""
    final = summary["final"]
    answers = {name: final.get(name) for name in COPIED_FIELDS if name != "nanopore_sequencing_date"}
    answers["nanopore_sequencing_date"] = final["run_date"]
    for name in ("epi_to_me_version", "sequencing_delayed_others"):
        answers[name] = answers[name] or ""
    reasons = answers.get("sequencing_delayed_reasons") or []
    answers["sequencing_delayed_reasons"] = NanoporeSequencingDelayedReasons.objects.filter(pk__in=[r.pk for r in reasons])
    return answers


def option_ids():
    """The option ids the run cards' show/hide needs (they can differ between databases)."""
    failed = NanoporeSequencingResults.objects.filter(value=FAILED_RESULT_VALUE).values_list("pk", flat=True).first()
    other = NanoporeSequencingDelayedReasons.objects.filter(value=OTHER_REASON).values_list("pk", flat=True).first()
    return {"failed": failed or "", "other": other or "", "yes": YES}


def saved_runs_changed(formset):
    """A run already saved is changed or removed: like any saved answer, that needs a reason."""
    for form in formset.forms:
        if not form.instance.pk:
            continue
        if form.data.get(f"{form.prefix}-DELETE"):
            return True
        if any(name != "DELETE" for name in form.changed_data):
            return True
    return False


def save_runs(formset, record, user, reason=""):
    formset.instance = record
    for run in formset.save(commit=False):
        if reason:
            run._change_reason = reason  # kept with the run's own history
        run.outcome = FAILED if _failed(run.nanopore_results) else PASSED
        run.updated_by = user
        if run.pk is None:
            run.created_by = user
        run.save()
    formset.save_m2m()
    for run in formset.deleted_objects:
        run.delete()


def export_columns(record):
    """Per-participant export columns: number of runs, first and final run dates."""
    if record is None:
        return ["", "", ""]
    runs = list(record.nanopore_runs.all())
    if not runs:
        return ["", "", ""]
    dates = sorted(r.run_date for r in runs)
    passed = sorted(r.run_date for r in runs if r.outcome == PASSED)
    return [len(runs), dates[0], (passed or dates)[-1]]


EXPORT_HEADER = ["nanopore_runs", "nanopore_first_run_date", "nanopore_final_run_date"]
