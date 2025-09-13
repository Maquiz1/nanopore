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

class RegimenChangesDeleteView(LoginRequiredMixin, DeleteView):
    model = RegimenChanges

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj_id = obj.id
        obj.delete()
        if self.request.headers.get("HX-Request") or self.request.headers.get("X-Requested-With"):
            return JsonResponse({"success": True, "message": "Regimen change deleted!", "regimen_id": obj_id})
        return super().delete(request, *args, **kwargs)
