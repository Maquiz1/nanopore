from django.contrib import admin
from .models import Disease, Competence,YesNo,YesNoNA


@admin.register(YesNo)
class YesNoAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(YesNoNA)
class YesNoNAAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

class CompetenceInline(admin.TabularInline):
    model = Competence
    extra = 1  # Number of empty forms to display

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [CompetenceInline]

@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'disease']
