# nanopore/views/regimen/regimen_views.py
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from nanopore.models import RegimenChanges, Screening
from nanopore.forms.regimen.regimenform import RegimenChangesForm

# nanopore/views/regimen/regimen_views.py
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy

class RegimenChangesUpdateView(LoginRequiredMixin, UpdateView):
    model = RegimenChanges
    form_class = RegimenChangesForm
    template_name = "nanopore/regimen/regimen_modal_form.html"

    def get_success_url(self):
        return reverse_lazy("nanopore:form-status-list")

class RegimenChangesDeleteView(LoginRequiredMixin, DeleteView):
    model = RegimenChanges
    template_name = "nanopore/regimen/regimen_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("nanopore:form-status-list")
