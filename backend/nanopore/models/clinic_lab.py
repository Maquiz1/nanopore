from django.db import models
from django.contrib.auth import get_user_model
from . import Screening
from options.models import (
    XpertMTB,
    YesNo, # Assuming this model exists
    SampleReason,  # Assuming this model exists
    SampleNumber,
    SampleAppearance,  # Renamed to avoid conflict
    AFBTechnique,
    AFBMicroscopyResult,
    XpertMTB,
    XpertRIF,
    NoSPCResult
)

User = get_user_model()

class ClinicLaboratory(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="clinic_laboratory")
    
    # pid = models.CharField(max_length=255, blank=True, null=True)
    
    # Sputum sample
    sample_received = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_sample_received")
    sample_reason = models.ForeignKey(SampleReason, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_sample_reason")
    other_reason = models.TextField(max_length=255, blank=True, null=True)
    new_sample = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_new_sample")
    new_reason = models.TextField(max_length=255, blank=True, null=True)
    number_received = models.ForeignKey(SampleNumber, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_number_received")
    
    # Sputum sample details
    date_sample1_collected = models.DateField(blank=True, null=True)
    date_sample1_received = models.DateField(blank=True, null=True)
    appearance_sample1 = models.ForeignKey(SampleAppearance, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_appearance_sample1")
    sample1_volume = models.CharField(max_length=255, blank=True, null=True)
    date_sample2_collected = models.DateField(blank=True, null=True)
    date_sample2_received = models.DateField(blank=True, null=True)
    appearance_sample2 = models.ForeignKey(SampleAppearance, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_appearance_sample2")
    sample2_volume = models.CharField(max_length=255, blank=True, null=True)
    
    # AFB Microscopy
    afb_microscopy_conducted = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_afb_microscopy_conducted")
    afb_a_date = models.DateField(blank=True, null=True)
    technique_a = models.ForeignKey(AFBTechnique, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_technique_a")
    afb_a_results = models.ForeignKey(AFBMicroscopyResult, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_afb_a_results")

    afb_b_date = models.DateField(blank=True, null=True)
    technique_b = models.ForeignKey(AFBTechnique, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_technique_b")
    afb_b_results = models.ForeignKey(AFBMicroscopyResult, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_afb_b_results")

    # Xpert MTB/RIF (Ultra) Test
    xpert_mtb_rif_conducted = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_xpert_mtb_rif_conducted")
    xpert_date = models.DateField(blank=True, null=True)
    xpert_mtb = models.ForeignKey(XpertMTB, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_xpert_mtb")
    error_code = models.IntegerField(blank=True, null=True)
    xpert_rif = models.ForeignKey(XpertRIF, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_xpert_rif")
    ct_value = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    ct_na = models.ForeignKey(NoSPCResult, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_lab_ct_na")
   
    # Additional fields
    remarks = models.TextField(blank=True, null=True)
    
    # Auditing
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_labs_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_labs_updated")

    class Meta:
        ordering = ["-sample_received"]

    def __str__(self):
        return f"{self.date_sample1_collected} for {self.screening.pid}"
    
    
    