from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from nanopore.models import RegimenChanges, Screening
from nanopore.forms.regimen.regimenform import RegimenChangesForm

class RegimenChangesFormView(LoginRequiredMixin, View):
    form_class = RegimenChangesForm

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk:
            return get_object_or_404(RegimenChanges, pk=pk)
        return None

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        form = self.form_class(request.POST, instance=obj)

        if form.is_valid():
            regimen = form.save(commit=False)
            if not obj:
                # Create new
                screening_id = request.POST.get("screening_id")
                if screening_id:
                    regimen.screening = Screening.objects.get(pk=screening_id)
                    regimen.pid = regimen.screening.pid
                regimen.created_by = request.user
            # Update metadata
            regimen.updated_by = request.user
            regimen.save()
            
            return JsonResponse({
                "success": True,
                "message": "Regimen saved!" if not obj else "Regimen updated!",
                "regimen_id": regimen.id,
                "date": regimen.date.strftime("%Y-%m-%d") if regimen.date else "",
                "drug": regimen.drug,
                "changes": str(regimen.changes),
                "reason": str(regimen.reason),
                "specify": str(regimen.specify),
            })

        return JsonResponse({"success": False, "errors": form.errors}, status=400)
