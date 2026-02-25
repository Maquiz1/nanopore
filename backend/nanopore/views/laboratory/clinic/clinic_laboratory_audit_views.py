from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from nanopore.models import ClinicLaboratory

class ClinicLaboratoryAuditView(LoginRequiredMixin, DetailView):
    model = ClinicLaboratory
    template_name = "nanopore/laboratory/clinic/clinic_laboratory_audit.html"
    context_object_name = "object"

    def get_object(self):
        return get_object_or_404(ClinicLaboratory, pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        historical_records = obj.history.all().order_by('-history_date')
        changes = []

        # Map history_type symbols to readable labels
        history_type_map = {
            '+': 'Created',
            '~': 'Updated',
            '-': 'Deleted'
        }

        for i in range(len(historical_records) - 1):
            new_record = historical_records[i]
            old_record = historical_records[i + 1]

            delta = new_record.diff_against(old_record)

            for change in delta.changes:
                changes.append({
                    "field": change.field,
                    "old": str(change.old),
                    "new": str(change.new),
                    "changed_by": getattr(new_record.history_user, "get_full_name", lambda: str(new_record.history_user))(),
                    "changed_at": new_record.history_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "history_type": history_type_map.get(new_record.history_type, new_record.history_type)
                })

        context["changes"] = changes
        return context