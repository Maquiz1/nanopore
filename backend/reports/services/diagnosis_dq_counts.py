# reports/services/diagnosis_dq_counts.py
from django.apps import apps
from django.db.models import Q, Count
from utils.permissions import filter_queryset_by_user_role
from django.utils import timezone
from datetime import timedelta

def get_diagnosis_dq_counts(user, zone_id=None, site_id=None):
    Diagnosis = apps.get_model("nanopore", "Diagnosis")
    qs = Diagnosis.objects.select_related(
        "screening",
        "screening__site",
        "screening__site__district__region__zone",
    )

    qs = filter_queryset_by_user_role(user, qs, site_field="screening__site")

    if zone_id:
        qs = qs.filter(screening__site__district__region__zone_id=zone_id)
    if site_id:
        qs = qs.filter(screening__site_id=site_id)

    today = timezone.now().date()
    six_months_ago = today - timedelta(days=180)

    # Duplicate TB register numbers
    duplicate_tb_register_numbers = (
        qs.filter(tb_diagnosis=1, tb_treatment=1)
        .exclude(tb_register_number__isnull=True)
        .exclude(tb_register_number__exact="")
        .values("tb_register_number")
        .annotate(cnt=Count("id"))
        .filter(cnt__gt=1)
        .values_list("tb_register_number", flat=True)
    )
    duplicate_tb_register_number_qs = qs.filter(
        tb_diagnosis=1, tb_treatment=1, tb_register_number__in=duplicate_tb_register_numbers
    )

    # Long treatment patients (≥6 months)
    long_treatment_qs = qs.filter(tb_treatment=1, tb_treatment_date__lte=six_months_ago)

    # Pending TB outcomes
    pending_tb_outcome_qs = long_treatment_qs.filter(tb_outcome2__isnull=True)
    pending_tb_outcome_date_qs = long_treatment_qs.filter(tb_outcome2__in=[1,2,3,4,5], tb_outcome2_date__isnull=True)

    counts = {
        "missing_tb_diagnosis": qs.filter(tb_diagnosis__isnull=True).count(),
        "missing_tb_diagnosis_date": qs.filter(tb_diagnosis=1, tb_diagnosis_date__isnull=True).count(),
        "missing_tb_diagnosis_made": qs.filter(tb_diagnosis=1, tb_diagnosis_made__isnull=True).count(),
        "missing_tb_treatment": qs.filter(tb_diagnosis=1, tb_treatment__isnull=True).count(),
        "missing_diagnosis_made_other": qs.filter(tb_diagnosis=1, tb_diagnosis_made__value=96, diagnosis_made_other__isnull=True).count(),
        "missing_tb_diagnosed_clinically": qs.filter(tb_diagnosis=1, tb_diagnosis_made=1).annotate(clinical_count=Count("tb_diagnosed_clinically")).filter(clinical_count=0).count(),
        "missing_tb_clinically_other": qs.filter(tb_diagnosis=1, tb_diagnosis_made=1, tb_diagnosed_clinically__value=96, tb_clinically_other__isnull=True).distinct().count(),
        "missing_bacteriological_diagnosis": qs.filter(tb_diagnosis=1, tb_diagnosis_made=2, bacteriological_diagnosis__isnull=True).count(),
        "missing_clinician_received_date": qs.filter(tb_diagnosis=1, tb_diagnosis_made=2, clinician_received_date__isnull=True).count(),
        "missing_tb_other_diagnosis": qs.filter(tb_diagnosis=2, tb_other_diagnosis__isnull=True).count(),
        "missing_tb_diagnosis_made2": qs.filter(tb_diagnosis=2, tb_diagnosis_made2__isnull=True).count(),
        "missing_tb_other_specify": qs.filter(tb_diagnosis=2, tb_other_diagnosis__value=96, tb_other_specify__isnull=True).count(),
        "missing_tb_treatment_date": qs.filter(tb_treatment=1, tb_treatment_date__isnull=True).count(),
        "missing_tb_register_number": qs.filter(tb_treatment=1, tb_register_number__isnull=True).count(),
        "duplicate_tb_register_number": duplicate_tb_register_number_qs.count(),
        "missing_tb_regimen": qs.filter(tb_treatment=1, tb_regimen__isnull=True).count(),
        "missing_regimen_changed": qs.filter(tb_treatment=1, regimen_changed__isnull=True).count(),
        "missing_tb_facility": qs.filter(tb_treatment=2, tb_facility__isnull=True).count(),
        "missing_tb_reason": qs.filter(tb_treatment=96, tb_reason__isnull=True).count(),
        "pending_tb_outcome": pending_tb_outcome_qs.count(),
        "pending_tb_outcome_date": pending_tb_outcome_date_qs.count(),
    }

    counts["total_issues"] = sum(counts.values())
    return counts
