# reports/services/clinic_dq/clinic_dq.py
from . diagnosis_dq import get_diagnosis_queryset,get_diagnosis_dq,calc_months

__all__ = [
    "get_diagnosis_queryset",
    "get_diagnosis_dq",
    "calc_months",
]


