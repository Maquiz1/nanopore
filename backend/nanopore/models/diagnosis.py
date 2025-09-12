from django.db import models
from django.contrib.auth import get_user_model
from nanopore.models import Screening
from options.models import (
    YesNo,
    TBDiagnosisMade,
    DiagnosisBacteriological,
    DiagnosedClinically,
    TBTreatmentStarted,
    RegimenPrescribed,
    RegimenTypeOfChange,
    RegimenReasonForChange,
    TBTreatmentOutcome,
    TBOtherDiagnosis,
    TBOtherDiagnosisMade
    )


User = get_user_model()

class Diagnosis(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="diagnosis")  
    
    # Final diagnosis

    tb_diagnosis = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="tb_diagnosis")
    tb_diagnosis_date = models.DateField(blank=True, null=True)
    tb_diagnosis_made = models.ForeignKey(TBDiagnosisMade, on_delete=models.SET_NULL, blank=True, null=True, related_name="tb_diagnosis_made")
    diagnosis_made_other = models.TextField(max_length=255, blank=True, null=True)
    bacteriological_diagnosis = models.ForeignKey(DiagnosisBacteriological, on_delete=models.SET_NULL, blank=True, null=True, related_name="bacteriological_diagnosis")
    tb_diagnosed_clinically = models.ManyToManyField(DiagnosedClinically, blank=True, related_name="tb_diagnosed_clinically")
    tb_clinically_other = models.CharField(max_length=255, blank=True, null=True)
    
    clinician_received_date = models.DateField(blank=True, null=True)

    tb_treatment = models.ForeignKey(TBTreatmentStarted, on_delete=models.SET_NULL, blank=True, null=True, related_name="tb_treatment")
    tb_treatment_date = models.DateField(blank=True, null=True)
    tb_facility = models.CharField(max_length=255, blank=True, null=True)
    tb_reason = models.TextField(max_length=255, blank=True, null=True)

    tb_register_number = models.CharField(max_length=255, blank=True, null=True)
    tb_regimen = models.ForeignKey(RegimenPrescribed, on_delete=models.SET_NULL, blank=True, null=True, related_name="tb_regimen")
    tb_regimen_other = models.CharField(max_length=255, blank=True, null=True)
    regimen_changed = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="regimen_changed")

    # Treatment outcome

    tb_outcome2 = models.ForeignKey(TBTreatmentOutcome, on_delete=models.SET_NULL, blank=True, null=True, related_name="tb_outcome2")
    tb_outcome2_date = models.CharField(max_length=20, blank=True, null=True)


    # Treatment outcome

    tb_other_diagnosis = models.ForeignKey(TBOtherDiagnosis, on_delete=models.SET_NULL, blank=True, null=True, related_name="tb_other_diagnosis")
    tb_other_specify = models.CharField(max_length=255, blank=True, null=True)
    tb_diagnosis_made2 = models.ForeignKey(TBOtherDiagnosisMade, on_delete=models.SET_NULL, blank=True, null=True, related_name="tb_other_diagnosis_made")

    # additional fields
    remarks = models.TextField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="diagnoses_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="diagnoses_updated")

    class Meta:
        ordering = ["-tb_diagnosis_date"]

    def __str__(self):
        return f"Diagnosis for {self.screening.pid}: {self.tb_diagnosis_date}"
