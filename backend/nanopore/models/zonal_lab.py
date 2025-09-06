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
    culture_method = models.ManyToManyField(CultureMethod, blank=True, related_name="zonal_laboratory_culture_method")
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


    # #  culture isolate

    # culture_isolate = models.ForeignKey(YesNoNA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_culture_isolate")
    # isolate_date = models.DateField(null=True,blank=True)

    # # phenotypic DST
    # phenotypic_performed = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_phenotypic_performed")
    # phenotypic_date_performed = models.DateField(null=True,blank=True)
    # phenotypic_date_results = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_phenotypic_date_results")

    # # phenotypic DST RESULTS
    # rifampicin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_rifampicin_phenotypic_dst",db_index=False)
    # isoniazid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_isoniazid_phenotypic_dst",db_index=False)
    # levofloxacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_levofloxacin_phenotypic_dst",db_index=False)
    # moxifloxacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_moxifloxacin_phenotypic_dst",db_index=False)
    # bedaquiline = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_bedaquiline_phenotypic_dst",db_index=False)
    # linezolid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_linezolid_phenotypic_dst",db_index=False)
    # clofazimine = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_clofazimine_phenotypic_dst",db_index=False)
    # cycloserine = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_cycloserine_phenotypic_dst",db_index=False)
    # terizidone = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_terizidone_phenotypic_dst",db_index=False)
    # ethambutol = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_ethambutol_phenotypic_dst",db_index=False)
    # delamanid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_delamanid_phenotypic_dst",db_index=False)
    # pyrazinamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_pyrazinamide_phenotypic_dst",db_index=False)
    # imipenem = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_imipenem_phenotypic_dst",db_index=False)
    # cilastatin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_cilastatin_phenotypic_dst",db_index=False)
    # meropenem = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_meropenem_phenotypic_dst",db_index=False)
    # amikacin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_amikacin_phenotypic_dst",db_index=False)
    # streptomycin = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_streptomycin_phenotypic_dst",db_index=False)
    # ethionamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_ethionamide_phenotypic_dst",db_index=False)
    # prothionamide = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_prothionamide_phenotypic_dst",db_index=False)
    # para_aminosalicylic_acid = models.ForeignKey(PhenotypicDSTResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_para_aminosalicylic_acid_phenotypic_dst",db_index=False)


    # # Xpert XDR
    # xpert_xdr_performed = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_xpert_xdr_performed")
    # xpert_xdr_date_performed = models.DateField(null=True,blank=True)

    # # Xpert XDR RESULTS
    # xpert_xdr_isoniazid = models.ForeignKey(XpertXDRResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_isoniazid_xpert_xdr",db_index=False)
    # xpert_xdr_fluoroquinolones = models.ForeignKey(XpertXDRResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_fluoroquinolones_xpert_xdr",db_index=False)
    # xpert_xdr_amikacin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_amikacin_xpert_xdr",db_index=False)
    # xpert_xdr_kanamycin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_kanamycin_xpert_xdr",db_index=False)
    # xpert_xdr_capreomycin = models.ForeignKey(XpertXDRResultsThree, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_capreomycin_xpert_xdr",db_index=False)
    # xpert_xdr_ethionamide2 = models.ForeignKey(XpertXDRResultsTwo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_ethionamide2_xpert_xdr",db_index=False)

    # # First-Line LPA
    # first_line_lpa = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_first_line_lpa")
    # first_line_lpa_date = models.DateField(null=True,blank=True)
    # first_line_drugs = models.ForeignKey(FirstLineDrugs, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_first_line_drugs")
    # lpa1_mtb = models.ForeignKey(MTBResultsLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_mtb")
    # lpa1_rif = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_rif")
    # lpa1_inh = models.ForeignKey(INHResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa1_inh")

    # # Second-Line LPA
    # second_line_lpa = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_second_line_lpa")
    # second_line_lpa_date = models.DateField(null=True,blank=True)
    # second_line_drugs = models.ForeignKey(SecondLineDrugs, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_second_line_drugs")
    # lpa2_mtb = models.ForeignKey(MTBResultsLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_mtb")
    # lpa2_rfluoroquinolones = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_rfluoroquinolones")
    # lpa2_aminoglycosides = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_aminoglycosides")
    # lpa2_kanamycin = models.ForeignKey(RIFResultLPA, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_lpa2_kanamycin")

    # # Nanopore sequencing
    # nanopore_done = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nanopore_done")
    # sequencing_results = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_sequencing_results")
    # epi_to_me = models.ForeignKey(YesNo, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_epi_to_me")
    # epi_to_me_version = models.CharField(max_length=255,null=True,blank=True)

    # # Nanopore sequencing Results

    # nano_amikacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_amikacin",db_index=False)
    # nano_bedaquiline = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_bedaquiline",db_index=False)
    # nano_capreomycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_capreomycin",db_index=False)
    # nano_clofazimine = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_clofazimine",db_index=False)
    # nano_delamanid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_delamanid",db_index=False)
    # nano_ethambutol = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_ethambutol",db_index=False)
    # nano_ethionamide = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_ethionamide",db_index=False)
    # nano_isoniazid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_isoniazid",db_index=False)
    # nano_kanamycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_kanamycin",db_index=False)
    # nano_levofloxacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_levofloxacin",db_index=False)
    # nano_linezolid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_linezolid",db_index=False)
    # nano_moxifloxacin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_moxifloxacin",db_index=False)
    # nano_pretomanid = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_pretomanid",db_index=False)
    # nano_pyrazinamide = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_pyrazinamide",db_index=False)
    # nano_rifampicin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_rifampicin",db_index=False)
    # nano_streptomycin = models.ForeignKey(NanoporeResults, on_delete=models.SET_NULL,null=True,blank=True, related_name="zonal_laboratory_nano_streptomycin",db_index=False)

    # # nano_cycloserine = models.ForeignKey(NanoporeResults, on_delete=models.PROTECT, related_name="enrollment_cough2weeks")
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
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.test_name} for {self.screening.pid} (Zonal Lab)"
