from django.contrib import admin
from .models import (
    YesNoNA,
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
    PositiveNegativeNA,
    PositiveNegative,
    DiseasesMedicalConditions,
    SampleReason,
    SampleNumber,
    SampleAppearance,
    AFBTechnique,
    AFBMicroscopyResult,
    XpertMTB,
    XpertRIF,
    NoSPCResult,
    TBDiagnosisMade,
    DiagnosisBacteriological,
    DiagnosedClinically,
    TBTreatmentStarted,
    RegimenPrescribed,
    RegimenTypeOfChange,
    RegimenReasonForChange,
    TBTreatmentOutcome,
    
    # ZONAL LABS
    CultureMethod,
    MicroscopyType,
    CultureMicroscopyResults,
    LJCultureResult,
    MGITCultureResult,
    PhenotypicDSTResults,
    XpertXDRResults,
    XpertXDRResultsThree,
    XpertXDRResultsTwo,
    FirstLineDrugs,
    SecondLineDrugs,
    MTBResultsLPA,
    RIFResultLPA,
    INHResultLPA,
    NanoporeResults,
    
)

@admin.register(YesNo)
class YesNoAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)

@admin.register(YesNoNA)
class YesNoNAAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)

@admin.register(YesNoUnknown)
class YesNoUnknownAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)

@admin.register(CategoryTreated)
class CategoryTreatedAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(Unknown)
class UnknownAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
@admin.register(MonthUnknown)
class MonthUnknownAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(YearUnknown)
class YearUnknownAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
@admin.register(MonthYearUnknown)
class MonthYearUnknownAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)

@admin.register(DrDsTB)
class DrDsTBAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
@admin.register(TreatmentRegimen)
class TreatmentRegimenAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)


@admin.register(TreatmentOutcome)
class TreatmentOutcomeAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(PositiveNegativeUnknown)
class PositiveNegativeUnknownAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
@admin.register(PositiveNegativeNA)
class PositiveNegativeNAAdmin(admin.ModelAdmin):        
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(PositiveNegative)
class PositiveNegativeAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)


@admin.register(DiseasesMedicalConditions)
class DiseasesMedicalConditionsAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
@admin.register(SampleReason)
class SampleReasonAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(SampleNumber)
class SampleNumberAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
@admin.register(SampleAppearance)
class SampleAppearanceAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(AFBTechnique)
class AFBTechniqueAdmin(admin.ModelAdmin):      
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(AFBMicroscopyResult)
class AFBMicroscopyResultAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(XpertMTB)
class XpertMTBAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(XpertRIF)
class XpertRIFAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)


@admin.register(NoSPCResult)
class NoSPCResultAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
@admin.register(TBDiagnosisMade)
class TBDiagnosisMadeAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    

@admin.register(DiagnosisBacteriological)
class DiagnosisBacteriologicalAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(DiagnosedClinically)
class DiagnosedClinicallyAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(TBTreatmentStarted)
class TBTreatmentStartedAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(RegimenPrescribed)
class RegimenPrescribedAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(RegimenTypeOfChange)
class RegimenTypeOfChangeAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)   
    
    
@admin.register(RegimenReasonForChange)
class RegimenReasonForChangeAdmin(admin.ModelAdmin):    
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
    
@admin.register(TBTreatmentOutcome)
class TBTreatmentOutcomeAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)

    
    
# ZONAL LAB MODELS  


@admin.register(CultureMethod)
class CultureMethodAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
      
@admin.register(MicroscopyType)
class MicroscopyTypeAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(CultureMicroscopyResults)
class CultureMicroscopyResultsAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(LJCultureResult)
class LJCultureResultAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
    
@admin.register(MGITCultureResult)
class MGITCultureResultAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(PhenotypicDSTResults)
class PhenotypicDSTResultsAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(XpertXDRResults)
class XpertXDRResultsAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(XpertXDRResultsThree)
class XpertXDRResultsThreeAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(XpertXDRResultsTwo)
class XpertXDRResultsTwoAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(FirstLineDrugs)
class FirstLineDrugsAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(SecondLineDrugs)
class SecondLineDrugsAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(MTBResultsLPA)
class MTBResultsLPAAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(RIFResultLPA)
class RIFResultLPAAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
    
@admin.register(INHResultLPA)
class INHResultLPAAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    
@admin.register(NanoporeResults)
class NanoporeResultsAdmin(admin.ModelAdmin):
    list_display = ('value', 'name', 'created_at')
    list_filter = ('value',)
    search_fields = ('name',)
    ordering = ('value',)
    

