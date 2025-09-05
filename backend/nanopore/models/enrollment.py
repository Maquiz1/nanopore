from django.db import models
from django.contrib.auth import get_user_model
from nanopore.models.screening import Screening  # Linking to your Screening model
from demographic.models import  Sex
from clinical.models import YesNo

User = get_user_model()

class Enrollment(models.Model):
    # Link to Screening
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="enrollment")
    # pid = models.CharField(max_length=255)  # Keep PID for reference

    # Fields from your table
    enrollment_date = models.DateField(blank=True, null=True)
    # sex = models.ForeignKey(Sex, on_delete=models.SET_NULL, null=True, blank=True)
    # dob = models.DateField()
    # age = models.IntegerField()

    # cough2weeks = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_cough2weeks")
    # poor_weight = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_poor_weight")
    # coughing_blood = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_coughing_blood")
    # unexplained_fever = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_unexplained_fever")
    # night_sweats = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_night_sweats")
    # neck_lymph = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_neck_lymph")
    # date_information_collected = models.DateField(blank=True, null=True)


    # history_tb = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_history_tb")
    # tx_previous = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_tx_previous")
    # tx_month = models.IntegerField(blank=True, null=True)
    # tx_year = models.IntegerField(blank=True, null=True)
    # tx_unknown_year = models.BooleanField(blank=True, null=True)
    # tx_unknown_month = models.BooleanField(blank=True, null=True)
    # dr_ds = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_dr_ds")
    # tb_category = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_tb_category")
    # tb_category_specify = models.TextField(max_length=255, blank=True, null=True)
    # relapse_years = models.IntegerField(blank=True, null=True)
    # ltf_months = models.IntegerField(blank=True, null=True)
    # ltf_months_unknown = models.BooleanField(blank=True, null=True)
    # tb_regimen = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_tb_regimen")
    # tb_regimen_specify = models.TextField(max_length=255, blank=True, null=True)
    # regimen_months = models.IntegerField(blank=True, null=True)
    # regimen_months_unknown = models.BooleanField(blank=True, null=True)
    # tb_otcome = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_tb_outcome")
    # hiv_status = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_hiv_status")
    # immunosuppressive = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_immunosuppressive")
    # immunosuppressive_diseases = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_immunosuppressive_diseases")
    # immunosuppressive_specify = models.TextField(max_length=255, blank=True, null=True)
    # other_diseases = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_other_diseases")
    # diseases_medical = models.ManyToManyField(MedicalCondition, blank=True, related_name="enrollment_diseases_medical")
    # diseases_specify = models.TextField(max_length=255, blank=True, null=True)

    # sputum_collected = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_sputum_collected")
    # sputum_date = models.DateField(blank=True, null=True)
    # sputum_reasons = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollment_sputum_reasons")
    
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="enrollments_updated")


    class Meta:
        ordering = ["-enrollment_date"]

    def __str__(self):
        return f"Enrollment {self.enrollment_id or self.pid}"
