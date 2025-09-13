# nanopore/views/regimen/regimen_views.py
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from nanopore.models import RegimenChanges, Screening
from nanopore.forms.regimen.regimenform import RegimenChangesForm


class RegimenChangesCreateView(LoginRequiredMixin, CreateView):
    model = RegimenChanges
    form_class = RegimenChangesForm
    template_name = "nanopore/regimen/regimen_modal_form.html"
    success_url = reverse_lazy("nanopore:form-status-list")

    def form_valid(self, form):
        regimen = form.save(commit=False)

        screening_id = self.request.POST.get("screening_id")
        if screening_id:
            regimen.screening = get_object_or_404(Screening, pk=screening_id)
            regimen.pid = regimen.screening.pid

        regimen.created_by = self.request.user
        regimen.updated_by = self.request.user
        regimen.save()

        # If HTMX / AJAX request, return JSON including regimen info for table
        if self.request.headers.get("X-Requested-With"):
            regimen_data = {
                "id": regimen.id,
                "date": regimen.date.strftime("%Y-%m-%d") if regimen.date else "",
                "drug": regimen.drug or "",
                "changes": str(regimen.changes) if regimen.changes else "",
                "reason": str(regimen.reason) if regimen.reason else "",
                "edit_url": reverse_lazy("nanopore:regimen-change-edit", args=[regimen.id]),
                "delete_url": reverse_lazy("nanopore:regimen-change-delete", args=[regimen.id]),
            }
            return JsonResponse({
                "success": True,
                "message": "Regimen change saved!",
                "regimen": regimen_data
            })

        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("X-Requested-With"):
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)
