from django import forms
from django.core.exceptions import ValidationError

REASON = "reason_for_change"
# Filled by the system, not answers: calculated on save or set by the view
NOT_ANSWERS = {"eligible", "created_by", "updated_by", "created_at", "updated_at"}


def _blank(value):
    return value in (None, [], (), set()) or (isinstance(value, str) and not value.strip())


class ReasonForChangeMixin:
    """
    Changing or removing an answer that was already saved needs a reason; it is kept
    with the record's change history (nanopore/history.py). Entering a form, or filling
    a question that was still empty, doesn't.
    Put it before forms.ModelForm: class XForm(ReasonForChangeMixin, forms.ModelForm).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if REASON not in self.fields:
            self.fields[REASON] = forms.CharField(
                required=False, label="Reason for change",
                widget=forms.Textarea(attrs={"class": "form-control", "rows": 2,
                                             "placeholder": "Why is this saved answer being changed?"}),
            )

    def changed_answers(self):
        """Answers that had a value and now differ. Filling an empty question is not a correction."""
        changed = []
        for name in self.changed_data:
            if name == REASON or name in NOT_ANSWERS:
                continue
            initial = self[name].initial
            if _blank(initial):
                continue
            posted = self[name].data
            if isinstance(initial, str) and isinstance(posted, str) and initial.strip() == posted.strip():
                continue  # only spaces around it differ
            changed.append(name)
        return changed

    def clean_reason_for_change(self):
        reason = (self.cleaned_data.get(REASON) or "").strip()
        if self.instance.pk and not reason and self.changed_answers():
            raise ValidationError("Required when changing an answer that was already saved.")
        return reason

    def apply_change_reason(self, record):
        """Hand the reason to the history entry this save makes."""
        reason = self.cleaned_data.get(REASON)
        if reason:
            record._change_reason = reason
        return record
