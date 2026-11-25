"""
One Nanopore sequencing run of a participant's sample (Zonal Lab section 7, question 20(b)).

A sample can be sequenced several times until a run passes. Every run is kept here; the
Zonal Lab's own Nanopore answers stay the final result: the passing run's date, its EPI2ME
analysis and its results (nanopore/nanopore_runs.py keeps them in step).
"""
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models

from nanopore.history import tracked

User = get_user_model()

PASSED, FAILED = "passed", "failed"
OUTCOMES = ((PASSED, "Passed"), (FAILED, "Failed"))

FAILURE_REASONS = (
    ("low_dna", "Low DNA / poor library yield"),
    ("flow_cell", "Flow cell problem (few active pores)"),
    ("library", "Library preparation problem"),
    ("contamination", "Contamination"),
    ("other", "Other, specify"),
)


class NanoporeRun(models.Model):
    history = tracked(m2m_fields=("sequencing_delayed_reasons",))
    zonal_lab = models.ForeignKey("nanopore.ZonalLaboratory", on_delete=models.CASCADE, related_name="nanopore_runs")
    run_date = models.DateField()
    outcome = models.CharField(max_length=10, choices=OUTCOMES)  # from 21(e): Failed is a failed run, any other result passed
    failure_reason = models.CharField(max_length=20, choices=FAILURE_REASONS, blank=True)
    failure_other = models.CharField(max_length=255, blank=True)
    # The lab's own run number, NN/YY: restarts each year (02/26, 30/26)
    run_number = models.CharField("Run number", max_length=7, validators=[RegexValidator(
        r"^\d{2}/\d{2}$", "Write the run number as NN/YY, e.g. 02/26.")])
    # 21(a)-(d) for this run: its EPI2ME analysis (the final run's answers are copied to the Zonal Lab)
    epi_to_me = models.ForeignKey("options.YesNo", on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    epi_to_me_date = models.DateField(null=True, blank=True)
    epi_to_me_version = models.CharField(max_length=100, blank=True)
    sequencing_results = models.ForeignKey("options.YesNo", on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    # 21(e)-(h) for this run: its result (Failed means the run failed) and any delay
    nanopore_results = models.ForeignKey("options.NanoporeSequencingResults", on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    sequencing_delayed = models.ForeignKey("options.YesNo", on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    sequencing_delayed_days = models.PositiveIntegerField(null=True, blank=True)
    sequencing_delayed_reasons = models.ManyToManyField("options.NanoporeSequencingDelayedReasons", blank=True, related_name="+")
    sequencing_delayed_others = models.CharField(max_length=255, blank=True)
    run_id = models.CharField("Run ID / flow cell ID", max_length=100, blank=True,
                              help_text="Optional: the MinKNOW run ID or flow cell ID, to trace the raw data.")

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="nanopore_runs_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="nanopore_runs_updated")

    class Meta:
        ordering = ["run_date", "pk"]  # run 1, 2, 3... by date, then in the order entered

    def __str__(self):
        return f"{self.run_date} {self.get_outcome_display()}"

    @property
    def number(self):
        """The participant's attempt: 1, 2, 3... in date order (not stored, so deleting a mistaken run leaves no gap)."""
        runs = list(self.zonal_lab.nanopore_runs.values_list("pk", flat=True))
        return runs.index(self.pk) + 1 if self.pk in runs else None
