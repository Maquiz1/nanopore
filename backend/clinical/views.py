from django.views.generic import ListView, DetailView
from .models import Disease, Competence

class DiseaseListView(ListView):
    model = Disease
    template_name = 'clinical/disease_list.html'
    context_object_name = 'diseases'

class DiseaseDetailView(DetailView):
    model = Disease
    template_name = 'clinical/disease_detail.html'
    context_object_name = 'disease'

class CompetenceDetailView(DetailView):
    model = Competence
    template_name = 'clinical/competence_detail.html'
    context_object_name = 'competence'
