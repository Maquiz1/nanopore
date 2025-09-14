from django.db import models
from django.contrib.auth import get_user_model
from nanopore.models.screening import Screening  # Linking to your Screening model
from demographic.models import Sex
from options.models import (
    YesNo, 
    YesNoUnknown,
    CategoryTreated,
    Unknown,
    MonthUnknown,
    YearUnknown,
    MonthYearUnknown,
    DrDsTB,
    TreatmentRegimen,
    TreatmentOutcome,
    PositiveNegativeUnknown,
    DiseasesMedicalConditions,  # Assuming this model exists
)
import datetime

User = get_user_model()

class Enrollment(models.Model):
    # Link to Screening
    screening = models.OneToOneField(
        Screening, on_delete=models.CASCADE, related_name="enrollment"
    )
    enrollment_date = models.DateField()

    # Reason(s) for being regarded as presumptive TB patient at initial assessment

    cough2weeks = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    poor_weight = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_poor_weight")
    coughing_blood = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_coughing_blood")
    unexplained_fever = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_unexplained_fever")
    night_sweats = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_night_sweats")
    neck_lymph = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_neck_lymph")
    history_tb = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_history_tb")

    date_information_collected = models.DateField()

    # History of TB and previous treatment
    tx_previous = models.ForeignKey(YesNoUnknown, on_delete=models.SET_NULL, blank=True, null=True, related_name="enrollment_tx_previous")
    tb_category = models.ForeignKey(CategoryTreated, on_delete=models.SET_NULL, blank=True, null=True, related_name="enrollment_tb_category")
    tb_category_specify = models.TextField(max_length=255, blank=True, null=True)
    tx_month = models.IntegerField(blank=True, null=True)
    # tx_unknown_month = models.ManyToManyField(MonthUnknown, blank=True, related_name="enrollment_tx_unknown_month")
    tx_unknown_month = models.BooleanField(default=False)
    tx_year = models.IntegerField(blank=True, null=True)
    # tx_unknown_year = models.ManyToManyField(YearUnknown, blank=True, related_name="enrollment_tx_unknown_year")
    tx_unknown_year = models.BooleanField(default=False)
    dr_ds = models.ForeignKey(DrDsTB, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_dr_ds")
    ltf_months = models.IntegerField(blank=True, null=True)
    # ltf_months_unknown = models.ManyToManyField(MonthUnknown, blank=True, related_name="enrollment_ltf_months_unknown")
    ltf_months_unknown = models.BooleanField(default=False)
    tb_regimen = models.ForeignKey(TreatmentRegimen, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_tb_regimen")
    tb_regimen_specify = models.TextField(max_length=255, blank=True, null=True)
    regimen_months = models.IntegerField(blank=True, null=True)
    # regimen_months_unknown = models.ManyToManyField(MonthUnknown, blank=True, related_name="enrollment_regimen_months_unknown")
    regimen_months_unknown = models.BooleanField(default=False)
    tb_otcome = models.ForeignKey(TreatmentOutcome, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_tb_outcome")

    # Health-related conditions
    hiv_status = models.ForeignKey(PositiveNegativeUnknown, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_hiv_status")
    other_diseases = models.ForeignKey(YesNoUnknown, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_other_diseases")
    diseases_medical = models.ManyToManyField(DiseasesMedicalConditions, blank=True, related_name="enrollment_diseases_medical")
    diseases_specify = models.TextField(max_length=255, blank=True, null=True)

    # Samples collections
    sputum_collected = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_sputum_collected")
    sputum_date = models.DateField(blank=True, null=True)
    sputum_reasons = models.TextField(blank=True, null=True)


    # ADDITIONAL COLUMNS
    remarks = models.TextField(blank=True, null=True)
    
    # AUDITING 

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="enrollments_updated")

    class Meta:
        ordering = ["-enrollment_date"]

    def __str__(self):
        return f"Enrollment for {self.screening.pid}"
