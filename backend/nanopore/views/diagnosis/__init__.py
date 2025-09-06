from .diagnosis_list import DiagnosisListView
from .diagnosis_detail import DiagnosisDetailView
from .diagnosis_create import DiagnosisCreateView
from .diagnosis_update import DiagnosisUpdateView
from .diagnosis_delete import DiagnosisDeleteView
from .diagnosis_form_view import DiagnosisFormView


__all__ = [
    "DiagnosisListView",
    "DiagnosisDetailView",
    "DiagnosisCreateView",
    "DiagnosisUpdateView",
    "DiagnosisFormView",  # replaces both create and update views
    "DiagnosisDeleteView",
]
