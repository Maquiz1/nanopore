"""A record's change history (nanopore/history.py): who changed which answer, when, from where and why."""
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render
from django.views import View

from nanopore import history
from nanopore.models import ClinicLaboratory, Diagnosis, EdcsTblisZonal, Enrollment, RegimenChanges, Screening, ZonalLaboratory
from utils import access

# key -> (model, form it belongs to, lookup to its site, codebook form for the question labels, title)
FORMS = {
    "screening": (Screening, access.SCREENING, "site", "screening", "Screening"),
    "enrollment": (Enrollment, access.ENROLLMENT, "screening__site", "enrollment", "Enrollment"),
    "clinic_lab": (ClinicLaboratory, access.CLINIC_LAB, "screening__site", "clinic_lab", "Clinic Laboratory"),
    "zonal_lab": (ZonalLaboratory, access.ZONAL_LAB, "screening__site", "zonal_lab", "Zonal Laboratory"),
    "edcs_tblis": (EdcsTblisZonal, access.EDCS_TBLIS, "screening__site", "edcs_tblis", "EDCS / TBLIS"),
    "diagnosis": (Diagnosis, access.DIAGNOSIS, "screening__site", "diagnosis", "Diagnosis"),
    "regimen": (RegimenChanges, access.REGIMEN, "screening__site", "regimen", "Regimen change"),
}
TYPES = {"+": "Created", "~": "Changed", "-": "Deleted"}


def question_labels(codebook_key, model):
    from reports.codebook import CODEBOOK_FORMS
    labels = {field.name: str(field.verbose_name).capitalize() for field in model._meta.get_fields() if hasattr(field, "verbose_name")}
    form_class = CODEBOOK_FORMS[codebook_key][1]
    for name, field in form_class.base_fields.items():
        if field.label:
            labels[name] = str(field.label)
    return labels


class Values:
    """Readable answers: option names instead of ids, dates as yyyy-mm-dd."""

    def __init__(self):
        self.options = {}

    def name_of(self, model, pk):
        cache = self.options.setdefault(model, {})
        if pk not in cache:
            option = model._default_manager.filter(pk=pk).first()
            cache[pk] = str(option) if option is not None else f"#{pk} (deleted)"
        return cache[pk]

    def show(self, field, value):
        if value in (None, "", [], set()):
            return "—"
        if field.many_to_many:
            target = field.m2m_reverse_field_name()
            return "; ".join(sorted(self.name_of(field.related_model, row[target]) for row in value))
        if field.is_relation:
            return self.name_of(field.related_model, value)
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return value.isoformat() if hasattr(value, "isoformat") else str(value)


class RecordHistoryView(View):
    template_name = "nanopore/history/record_history.html"

    def get(self, request, form_key, pk):
        if form_key not in FORMS:
            raise Http404
        model, form, site_field, codebook_key, title = FORMS[form_key]
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not access.can_view(request.user, form):
            raise PermissionDenied
        record = access.scope_queryset(request.user, model._default_manager.filter(pk=pk), site_field).first()
        if record is None:
            raise Http404

        labels, values = question_labels(codebook_key, model), Values()
        fields = {field.name: field for field in (*model._meta.concrete_fields, *model._meta.many_to_many)}
        entries = list(record.history.select_related("history_user").order_by("history_date", "history_id"))
        shown, previous = [], None
        for entry in entries:
            changes = []
            if previous is not None and entry.history_type == "~":
                delta = entry.diff_against(previous, excluded_fields=history.IGNORED)
                for change in delta.changes:
                    field = fields.get(change.field)
                    if field is None or history._plain_answer(change.old) == history._plain_answer(change.new):
                        continue  # blank and empty are the same answer
                    changes.append({"question": labels.get(change.field, change.field), "name": change.field,
                                    "old": values.show(field, change.old), "new": values.show(field, change.new)})
            user = entry.history_user
            shown.append({
                "when": entry.history_date, "type": TYPES.get(entry.history_type, entry.history_type),
                "who": (user.get_full_name() or user.username) if user else "System",
                "source": entry.history_source or (history.STARTING_POINT if entry.history_type == "+" else ""),
                "reason": entry.history_change_reason or "", "changes": changes,
            })
            previous = entry
        shown.reverse()
        sources = sorted({row["source"] for row in shown if row["source"]})
        chosen = request.GET.get("source", "")
        if chosen in sources:
            shown = [row for row in shown if row["source"] == chosen]
        return render(request, self.template_name, {
            "record": record, "title": title, "entries": shown, "sources": sources, "chosen": chosen,
            "pid": getattr(getattr(record, "screening", None), "pid", None) or getattr(record, "pid", ""),
        })
