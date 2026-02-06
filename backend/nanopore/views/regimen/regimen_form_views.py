from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from nanopore.models import RegimenChanges, Screening
from nanopore.forms.regimen.regimenform import RegimenChangesForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages

class RegimenChangesFormView(LoginRequiredMixin, View):
    """
    Handles AJAX create/update for RegimenChanges
    """
    form_class = RegimenChangesForm

    def get_object(self):
        pk = self.request.POST.get("regimen_id") or self.kwargs.get("pk")
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
                    regimen.screening = get_object_or_404(Screening, pk=screening_id)
                    regimen.pid = regimen.screening.pid
                regimen.created_by = request.user
            # Always update metadata
            regimen.updated_by = request.user
            regimen.save()
            
            messages.success(request, "Enrollment saved successfully.")

            # Return all relevant data for JS to update modal/table
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


from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class RegimenChangesEditView(LoginRequiredMixin, View):
    """
    Fetch regimen data for modal edit (AJAX GET)
    """
    def get(self, request, pk, *args, **kwargs):
        regimen = get_object_or_404(RegimenChanges, pk=pk)
        data = {
            "fields": {
                "date": regimen.date.strftime("%Y-%m-%d") if regimen.date else "",
                "drug": regimen.drug,
                "changes": regimen.changes,
                "reason": regimen.reason,
                "specify": regimen.specify,
            }
        }
        return JsonResponse(data)


@method_decorator(csrf_exempt, name="dispatch")
class RegimenChangesDeleteView(LoginRequiredMixin, View):
    """
    AJAX Delete of a regimen change
    """
    def delete(self, request, pk, *args, **kwargs):
        try:
            regimen = get_object_or_404(RegimenChanges, pk=pk)
            regimen.delete()
            return JsonResponse({"success": True, "message": "Regimen deleted!"})
        except Exception as e:
            return JsonResponse({"success": False, "errors": str(e)}, status=400)
