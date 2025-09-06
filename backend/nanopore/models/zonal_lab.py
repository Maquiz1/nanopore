from django.db import models
from django.contrib.auth import get_user_model
from nanopore.models import Screening
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
User = get_user_model()

class ZonalLaboratory(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="zonal_laboratory")
    test_name = models.CharField(max_length=100)
    result = models.CharField(max_length=100, blank=True, null=True)
    test_date = models.DateField()
    
    
    culture_performed = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    culture_method = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    culture_results = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    date_sputum_received = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    appearance = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    sample_volume = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    unique_lab_no = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    microscopy_type = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    microscopy_date = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lj_inoculation_date = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    microscopy_results = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lj_results_date = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lj_results = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    mgit_inoculation_date = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    mgit_results_date = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    mgit_results = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    culture_isolate = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    isolate_date = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    # phenotypic DST
    phenotypic_performed = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    phenotypic_date_performed = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    phenotypic_date_results = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    # phenotypic DST RESULTS
    rifampicin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    isoniazid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    levofloxacin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    moxifloxacin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    bedaquiline = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    linezolid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    clofazimine = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    cycloserine = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    terizidone = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    ethambutol = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    delamanid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    pyrazinamide = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    imipenem = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    cilastatin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    amikacin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    streptomycin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    ethionamide = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    prothionamide = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    para_aminosalicylic_acid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    xpert_xdr_performed = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    isoniazid2 = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    fluoroquinolones = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    amikacin2 = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    kanamycin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    capreomycin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    ethionamide2 = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_rifampicin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_isoniazid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_levofloxacin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_moxifloxacin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_bedaquiline = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_linezolid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_clofazimine = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_cycloserine = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_terizidone = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_cilastatin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_ethambutol = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_delamanid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_pyrazinamide = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_imipenem = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_meropenem = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_amikacin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_streptomycin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_ethionamide = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_prothionamide = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_ethionamide = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_para_aminosalicylic_acid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_capreomycin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_kanamycin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_pretomanid = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    
    _1st_line_drugs = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    _2st_line_drugs = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    first_line_lpa = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    first_line_lpa_date = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    first_line_drugs = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    second_line_lpa = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    second_line_lpa_date = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    second_line_drugs = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    xpert_xdr_date_performed = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nanopore_done = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    sequencing_results = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    epi_to_me = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    epi_to_me_version = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa1_mtb = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa1_rif = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa1_inh = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa2_mtb = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa2_rfluoroquinolones = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa2_aminoglycosides = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa2_kanamycin = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")    
    
    # ADDITIONAL FIELDS
    remarks = models.TextField(blank=True, null=True)
    
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_updated")

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.test_name} for {self.screening.pid} (Zonal Lab)"
