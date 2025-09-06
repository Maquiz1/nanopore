from django.db import models
from django.contrib.auth import get_user_model
from nanopore.models import Screening
from options.models import (
    SampleAppearance,
    YesNo,
    CultureMethod,
    MicroscopyType,
    CultureMicroscopyResults,
    LJCultureResult,
    MGITCultureResult,
    YesNoNA,
    PhenotypicDSTResults,
    XpertXDRResults,
    XpertXDRResultsTwo, 
    XpertXDRResultsThree,
    FirstLineDrugs,
    SecondLineDrugs,
    MTBResultsLPA,
    RIFResultLPA,
    INHResultLPA,
    NanoporeResults
)
User = get_user_model()

class ZonalLaboratory(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="zonal_laboratory")
    test_name = models.CharField(max_length=100)
    result = models.CharField(max_length=100, blank=True, null=True)
    test_date = models.DateField()
    
    # NEW FIELDS
    # Specimen receipt
    date_sputum_received = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    appearance = models.ForeignKey(SampleAppearance, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    sample_volume = models.DecimalField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    unique_lab_no = models.CharField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")

    # Culture
    culture_performed = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    culture_method = models.ForeignKey(CultureMethod, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    microscopy_type = models.ForeignKey(MicroscopyType, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    microscopy_date = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    microscopy_results = models.ForeignKey(CultureMicroscopyResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")

    # LJ RESULTS
    lj_inoculation_date = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lj_results_date = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lj_results = models.ForeignKey(LJCultureResult, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    # MGIT RESULTS
    mgit_inoculation_date = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    mgit_results_date = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    mgit_results = models.ForeignKey(MGITCultureResult, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")


    #  culture isolate

    culture_isolate = models.ForeignKey(YesNoNA, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    isolate_date = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    # phenotypic DST
    phenotypic_performed = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    phenotypic_date_performed = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    phenotypic_date_results = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    # phenotypic DST RESULTS
    rifampicin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    isoniazid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    levofloxacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    moxifloxacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    bedaquiline = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    linezolid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    clofazimine = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    cycloserine = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    terizidone = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    ethambutol = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    delamanid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    pyrazinamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    imipenem = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    cilastatin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    meropenem = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    amikacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    streptomycin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    ethionamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    prothionamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")   
    para_aminosalicylic_acid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    
    # Xpert XDR
    xpert_xdr_performed = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    xpert_xdr_date_performed = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")

    # Xpert XDR RESULTS    
    isoniazid2 = models.ForeignKey(XpertXDRResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    fluoroquinolones = models.ForeignKey(XpertXDRResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    amikacin2 = models.ForeignKey(XpertXDRResultsThree, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    kanamycin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    capreomycin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    ethionamide2 = models.ForeignKey(XpertXDRResultsTwo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    # First-Line LPA    
    first_line_lpa = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    first_line_lpa_date = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    first_line_drugs = models.ForeignKey(FirstLineDrugs, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa1_mtb = models.ForeignKey(MTBResultsLPA, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa1_rif = models.ForeignKey(RIFResultLPA, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa1_inh = models.ForeignKey(INHResultLPA, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")

    
    # FiSecondrst-Line LPA   
    second_line_lpa = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    second_line_lpa_date = models.DateField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    second_line_drugs = models.ForeignKey(SecondLineDrugs, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa2_mtb = models.ForeignKey(MTBResultsLPA, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa2_rfluoroquinolones = models.ForeignKey(RIFResultLPA, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa2_aminoglycosides = models.ForeignKey(RIFResultLPA, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    lpa2_kanamycin = models.ForeignKey(RIFResultLPA, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")    

    # Nanopore sequencing   
    nanopore_done = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    sequencing_results = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    epi_to_me = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    epi_to_me_version = models.CharField(YesNo, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
 
     # Nanopore sequencing   Results
    nano_rifampicin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_isoniazid = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_levofloxacin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_moxifloxacin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_bedaquiline = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_linezolid = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_clofazimine = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_cycloserine = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_terizidone = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_cilastatin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_ethambutol = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_delamanid = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_pyrazinamide = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_imipenem = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_meropenem = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_amikacin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_streptomycin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_ethionamide = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_prothionamide = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_ethionamide = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_para_aminosalicylic_acid = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_capreomycin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_kanamycin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    nano_pretomanid = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    # ADDITIONAL FIELDS
    remarks = models.TextField(blank=True, null=True)
    
    # Auditing
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_updated")

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.test_name} for {self.screening.pid} (Zonal Lab)"
