from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from nanopore.models import ClinicLaboratory


class ClinicLaboratoryAuditView(LoginRequiredMixin, DetailView):
    model = ClinicLaboratory
    template_name = "nanopore/laboratory/clinic/clinic_laboratory_audit.html"
    context_object_name = "object"

    def get_object(self):
        return get_object_or_404(
            ClinicLaboratory,
            pk=self.kwargs.get("pk")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        # Oldest → Newest
        historical_records = list(
            obj.history.all().order_by("history_date")
        )

        changes = []

        history_type_map = {
            "+": "Created",
            "~": "Updated",
            "-": "Deleted",
        }

        for index, record in enumerate(historical_records):

            # Safe user display
            if record.history_user:
                user_display = (
                    record.history_user.get_full_name()
                    or record.history_user.username
                )
            else:
                user_display = "System"

            history_label = history_type_map.get(
                record.history_type,
                record.history_type
            )

            # ─────────────────────────────
            # HANDLE CREATED RECORD
            # ─────────────────────────────
            if index == 0:
                changes.append({
                    "field": "Record Created",
                    "old": "",
                    "new": "",
                    "changed_by": user_display,
                    "changed_at": record.history_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "history_type": history_label,
                    "reason": record.history_change_reason or "",
                })
                continue

            # ─────────────────────────────
            # HANDLE UPDATED / DELETED
            # ─────────────────────────────
            previous_record = historical_records[index - 1]
            delta = record.diff_against(previous_record)

            for change in delta.changes:
                changes.append({
                    "field": change.field,
                    "old": str(change.old) if change.old is not None else "",
                    "new": str(change.new) if change.new is not None else "",
                    "changed_by": user_display,
                    "changed_at": record.history_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "history_type": history_label,
                    "reason": record.history_change_reason or "",
                })

        # Newest first for display
        context["changes"] = reversed(changes)

        return context