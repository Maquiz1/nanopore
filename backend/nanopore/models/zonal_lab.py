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
    date_sputum_received = models.DateField(null=True, blank=True)
    appearance = models.ForeignKey(SampleAppearance, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_appearance")
    sample_volume = models.DecimalField(null=True, blank=True, max_digits=3, decimal_places=1)
    unique_lab_no = models.CharField(max_length=100, blank=True, null=True)

    # Culture
    culture_performed = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_culture_performed")
    culture_method = models.ForeignKey(CultureMethod, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_culture_method")
    microscopy_type = models.ForeignKey(MicroscopyType, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_culture_microscopy_type")
    microscopy_date = models.DateField(null=True, blank=True)
    microscopy_results = models.ForeignKey(CultureMicroscopyResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_culture_microscopy_results")

    # LJ RESULTS
    lj_inoculation_date = models.DateField(null=True,blank=True)
    lj_results_date = models.DateField(null=True,blank=True)
    lj_results = models.ForeignKey(LJCultureResult, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lj_results")

    # MGIT RESULTS
    mgit_inoculation_date = models.DateField(null=True,blank=True)
    mgit_results_date = models.DateField(null=True,blank=True)
    mgit_results = models.ForeignKey(MGITCultureResult, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_mgit_results")


    #  culture isolate

    culture_isolate = models.ForeignKey(YesNoNA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_culture_isolate")
    isolate_date = models.DateField(null=True,blank=True)

    # phenotypic DST
    phenotypic_performed = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_phenotypic_performed")
    phenotypic_date_performed = models.DateField(null=True,blank=True)
    phenotypic_date_results = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_phenotypic_date_results")

    # phenotypic DST RESULTS
    rifampicin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_rifampicin")
    isoniazid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_isoniazid")
    levofloxacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_levofloxacin")
    moxifloxacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_moxifloxacin")
    bedaquiline = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_bedaquiline")
    linezolid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_linezolid")
    clofazimine = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_clofazimine")
    cycloserine = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_cycloserine")
    terizidone = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_terizidone")
    ethambutol = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_ethambutol")
    delamanid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_delamanid")
    pyrazinamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_pyrazinamide")
    imipenem = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_imipenem")
    cilastatin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_cilastatin")
    meropenem = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_meropenem")
    amikacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_amikacin")
    streptomycin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_streptomycin")
    ethionamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_ethionamide")
    prothionamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_prothionamide")
    para_aminosalicylic_acid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_para_aminosalicylic_acid")


    # Xpert XDR
    xpert_xdr_performed = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_xpert_xdr_performed")
    xpert_xdr_date_performed = models.DateField(null=True,blank=True)

    # Xpert XDR RESULTS    
    isoniazid2 = models.ForeignKey(XpertXDRResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_isoniazid2")
    fluoroquinolones = models.ForeignKey(XpertXDRResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_fluoroquinolones")
    amikacin2 = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_amikacin2")
    kanamycin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_kanamycin")
    capreomycin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_capreomycin")
    ethionamide2 = models.ForeignKey(XpertXDRResultsTwo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_ethionamide2")

    # First-Line LPA
    first_line_lpa = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_first_line_lpa")
    first_line_lpa_date = models.DateField(null=True,blank=True)
    first_line_drugs = models.ForeignKey(FirstLineDrugs, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_first_line_drugs")
    lpa1_mtb = models.ForeignKey(MTBResultsLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_mtb")
    lpa1_rif = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_rif")
    lpa1_inh = models.ForeignKey(INHResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_inh")

    # Second-Line LPA
    second_line_lpa = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_second_line_lpa")
    second_line_lpa_date = models.DateField(null=True,blank=True)
    second_line_drugs = models.ForeignKey(SecondLineDrugs, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_second_line_drugs")
    lpa2_mtb = models.ForeignKey(MTBResultsLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_mtb")
    lpa2_rfluoroquinolones = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_rfluoroquinolones")
    lpa2_aminoglycosides = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_aminoglycosides")
    lpa2_kanamycin = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_kanamycin")

    # Nanopore sequencing
    nanopore_done = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nanopore_done")
    sequencing_results = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_sequencing_results")
    epi_to_me = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_epi_to_me")
    epi_to_me_version = models.CharField(max_length=255,null=True,blank=True)

    # Nanopore sequencing Results

    nano_amikacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_amikacin")
    nano_bedaquiline = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_bedaquiline")
    nano_capreomycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_capreomycin")
    nano_clofazimine = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_clofazimine")
    nano_delamanid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_delamanid")
    nano_ethambutol = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_ethambutol")
    nano_ethionamide = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_ethionamide")
    nano_isoniazid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_isoniazid")
    nano_kanamycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_kanamycin")
    nano_levofloxacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_levofloxacin")
    nano_linezolid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_linezolid")
    nano_moxifloxacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_moxifloxacin")
    nano_pretomanid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_pretomanid")
    nano_pyrazinamide = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_pyrazinamide")
    nano_rifampicin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_rifampicin")
    nano_streptomycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_streptomycin")

    # nano_cycloserine = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # nano_terizidone = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # nano_imipenem = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # nano_cilastatin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # nano_meropenem = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # nano_prothionamide = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # nano_ethionamide = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # nano_para_aminosalicylic_acid = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
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
