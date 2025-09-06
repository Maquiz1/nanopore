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
    NoSPCResult
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
