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
    # test_name = models.CharField(max_length=100)
    # result = models.CharField(max_length=100, blank=True, null=True)
    # test_date = models.DateField()
    
    # # NEW FIELDS
    # Specimen receipt
    date_sputum_received = models.DateField(null=True, blank=True)
    appearance = models.ForeignKey(SampleAppearance, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_appearance")
    sample_volume = models.DecimalField(null=True, blank=True, max_digits=3, decimal_places=1)
    unique_lab_no = models.CharField(max_length=100, blank=True, null=True)
    
    # Culture
    culture_performed = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_culture_performed")
    culture_method = models.ManyToManyField(CultureMethod, blank=True, related_name="zonal_laboratory_culture_method")
    microscopy_type = models.ForeignKey(MicroscopyType, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_culture_microscopy_type")
    microscopy_date = models.DateField(null=True, blank=True)
    microscopy_results = models.ForeignKey(CultureMicroscopyResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_culture_microscopy_results")

    # LJ RESULTS
    lj_inoculation_date = models.DateField(null=True, blank=True)
    lj_results_date = models.DateField(null=True, blank=True)
    lj_results = models.ForeignKey(LJCultureResult, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_lj_results")

    # MGIT RESULTS
    mgit_inoculation_date = models.DateField(null=True, blank=True)
    mgit_results_date = models.DateField(null=True, blank=True)
    mgit_results = models.ForeignKey(MGITCultureResult, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_mgit_results")

    # Culture isolate
    culture_isolate = models.ForeignKey(YesNoNA, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_culture_isolate")
    isolate_date = models.DateField(null=True, blank=True)

    # Phenotypic DST
    phenotypic_performed = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_phenotypic_performed")
    phenotypic_date_performed = models.DateField(null=True, blank=True)
    phenotypic_date_results = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_phenotypic_date_results")

    # Phenotypic DST RESULTS (no explicit db_index)
    rifampicin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_rifampicin_phenotypic_dst")
    isoniazid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_isoniazid_phenotypic_dst")
    levofloxacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_levofloxacin_phenotypic_dst")
    moxifloxacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_moxifloxacin_phenotypic_dst")
    bedaquiline = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_bedaquiline_phenotypic_dst")
    linezolid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_linezolid_phenotypic_dst")
    clofazimine = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_clofazimine_phenotypic_dst")
    cycloserine = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_cycloserine_phenotypic_dst")
    terizidone = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_terizidone_phenotypic_dst")
    ethambutol = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_ethambutol_phenotypic_dst")
    delamanid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_delamanid_phenotypic_dst")
    pyrazinamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_pyrazinamide_phenotypic_dst")
    imipenem = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_imipenem_phenotypic_dst")
    cilastatin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_cilastatin_phenotypic_dst")
    meropenem = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_meropenem_phenotypic_dst")
    amikacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_amikacin_phenotypic_dst")
    streptomycin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_streptomycin_phenotypic_dst")
    ethionamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_ethionamide_phenotypic_dst")
    prothionamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_prothionamide_phenotypic_dst")
    para_aminosalicylic_acid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_para_aminosalicylic_acid_phenotypic_dst")

    # Xpert XDR (no explicit db_index)
    xpert_xdr_performed = models.ForeignKey(YesNo, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_xpert_xdr_performed")
    xpert_xdr_date_performed = models.DateField(null=True, blank=True)
    xpert_xdr_isoniazid = models.ForeignKey(XpertXDRResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_isoniazid_xpert_xdr")
    xpert_xdr_fluoroquinolones = models.ForeignKey(XpertXDRResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_fluoroquinolones_xpert_xdr")
    xpert_xdr_amikacin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_amikacin_xpert_xdr")
    xpert_xdr_kanamycin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_kanamycin_xpert_xdr")
    xpert_xdr_capreomycin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_capreomycin_xpert_xdr")
    xpert_xdr_ethionamide = models.ForeignKey(XpertXDRResultsTwo, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_ethionamide_xpert_xdr")


 # First-Line LPA
    first_line_lpa = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_first_line_lpa")
    first_line_lpa_date = models.DateField(null=True,blank=True)
    first_line_drugs = models.ManyToManyField(FirstLineDrugs ,blank=True, related_name="zonal_laboratory_first_line_drugs")
    lpa1_mtb = models.ForeignKey(MTBResultsLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_mtb")
    lpa1_rif = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_rif")
    lpa1_inh = models.ForeignKey(INHResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_inh")

    # Second-Line LPA
    second_line_lpa = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_second_line_lpa")
    second_line_lpa_date = models.DateField(null=True,blank=True)
    second_line_drugs = models.ManyToManyField(SecondLineDrugs,blank=True, related_name="zonal_laboratory_second_line_drugs")
    lpa2_mtb = models.ForeignKey(MTBResultsLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_mtb")
    lpa2_rfluoroquinolones = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_rfluoroquinolones")
    lpa2_aminoglycosides = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_aminoglycosides")
    lpa2_kanamycin = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_kanamycin")

    # Nanopore sequencing
    nanopore_done = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nanopore_done")
    sequencing_results = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_sequencing_results")
    epi_to_me = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_epi_to_me")
    epi_to_me_version = models.CharField(max_length=255,null=True,blank=True)
    
    # Nanopore sequencing (no explicit db_index)
    nano_amikacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_amikacin")
    nano_bedaquiline = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_bedaquiline")
    nano_capreomycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_capreomycin")
    nano_clofazimine = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_clofazimine")
    nano_delamanid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_delamanid")
    nano_ethambutol = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_ethambutol")
    nano_ethionamide = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_ethionamide")
    nano_isoniazid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_isoniazid")
    nano_kanamycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_kanamycin")
    nano_levofloxacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_levofloxacin")
    nano_linezolid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_linezolid")
    nano_moxifloxacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_moxifloxacin")
    nano_pretomanid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_pretomanid")
    nano_pyrazinamide = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_pyrazinamide")
    nano_rifampicin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_rifampicin")
    nano_streptomycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_laboratory_nano_streptomycin")

    # # nano_terizidone = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # # nano_imipenem = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # # nano_cilastatin = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # # nano_meropenem = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # # nano_prothionamide = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # # nano_ethionamide = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    # # nano_para_aminosalicylic_acid = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
    
    # ADDITIONAL FIELDS
    remarks = models.TextField(blank=True, null=True)
    
    # Auditing
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_updated")

    class Meta:
        ordering = ["-date_sputum_received"]

    def __str__(self):
        return f"{self.test_name} for {self.screening.pid} (Zonal Lab)"
