from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import Disease, Competence

class DiseaseListView(LoginRequiredMixin, ListView):
    model = Disease
    template_name = 'clinical/disease_list.html'
    context_object_name = 'diseases'

class DiseaseDetailView(LoginRequiredMixin, DetailView):
    model = Disease
    template_name = 'clinical/disease_detail.html'
    context_object_name = 'disease'

class CompetenceDetailView(LoginRequiredMixin, DetailView):
    model = Competence
    template_name = 'clinical/competence_detail.html'
    context_object_name = 'competence'
