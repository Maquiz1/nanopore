from django.apps import apps
from django.db.models import Q, Count
from utils.permissions import filter_queryset_by_user_role
from django.utils import timezone
from dateutil.relativedelta import relativedelta


# Helper: calculate months on treatment
def calc_months(start_date, end_date):
    if not start_date:
        return None
    rd = relativedelta(end_date, start_date)
    return rd.years * 12 + rd.months


def get_diagnosis_queryset(user, zone_id=None, site_id=None):
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

    return qs


def get_diagnosis_dq(qs):
    today = timezone.now().date()
    six_months_ago = today - relativedelta(months=6)

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
    pending_tb_outcome_qs = long_treatment_qs.filter(tb_outcome2__isnull=True)
    pending_tb_outcome_date_qs = long_treatment_qs.filter(
        tb_outcome2__in=[1, 2, 3, 4, 5], tb_outcome2_date__isnull=True
    )

    # tb_diagnosis = 2 → all TB fields must be EMPTY
    tb_diag_filled_q = Q()
    char_fields = [
        "diagnosis_made_other",
        "tb_clinically_other",
        "tb_facility",
        "tb_reason",
        "tb_register_number",
        "tb_regimen_other",
    ]
    for field in char_fields:
        tb_diag_filled_q |= (~Q(**{f"{field}__isnull": True}) & ~Q(**{f"{field}": ""}))

    non_char_fields = [
        "tb_diagnosis_date",
        "tb_diagnosis_made",
        "bacteriological_diagnosis",
        "clinician_received_date",
        "tb_treatment",
        "tb_treatment_date",
        "tb_regimen",
        "regimen_changed",
        "tb_outcome2",
        "tb_outcome2_date",
    ]
    for field in non_char_fields:
        tb_diag_filled_q |= ~Q(**{f"{field}__isnull": True})

    tb_diag_m2m_q = Q(tb_diagnosed_clinically__isnull=False)

    missing_tb_diagnosis_2_should_be_empty = qs.filter(tb_diagnosis=2).filter(
        tb_diag_filled_q | tb_diag_m2m_q
    ).distinct()
    
    # tb_diagnosis = 1 → all Diagnosis other than TB fields must be EMPTY
    tb_tb_diagnosis_is_1_q = Q(tb_diagnosis=1) | Q(tb_diagnosis__value=1) | Q(tb_diagnosis__name__iexact="1")
    diag_other_than_tb_filled_q = Q()
    diag_other_than_tb_non_char_fields = [
        "tb_other_diagnosis",
        "tb_diagnosis_made2",
    ]
    for field in diag_other_than_tb_non_char_fields:
        diag_other_than_tb_filled_q |= ~Q(**{f"{field}__isnull": True})
        
    invalid_diag_other_than_tb_filled = qs.filter(
        tb_tb_diagnosis_is_1_q & diag_other_than_tb_filled_q
    )
    
    # tb_other_diagnosis = 1,2,4,5 → 12(a). If Other Mention ( or If Bacterial pneumonia, specify causative species if known): field must be EMPTY
    tb_other_diag_condition_q = (
        Q(tb_other_diagnosis__in=[1,2,4,5]) |
        Q(tb_other_diagnosis__value__in=[1,2,4,5]) |
        Q(tb_other_diagnosis__name__in=["1","2","4","5"])
    )

    mention_tb_other_specify_filled_q = (
        Q(tb_other_specify__isnull=False) &
        ~Q(tb_other_specify="")
    )

    invalid_mention_tb_other_specify_filled = qs.filter(
        tb_other_diag_condition_q & mention_tb_other_specify_filled_q
    )

    # ──────────────────────────────
    # Problem querysets
    # ──────────────────────────────
    problem_lists = {
        "missing_tb_diagnosis": qs.filter(tb_diagnosis__isnull=True),
        "missing_tb_diagnosis_date": qs.filter(tb_diagnosis=1, tb_diagnosis_date__isnull=True),
        "missing_tb_diagnosis_made": qs.filter(tb_diagnosis=1, tb_diagnosis_made__isnull=True),
        "missing_tb_treatment": qs.filter(tb_diagnosis=1, tb_treatment__isnull=True),
        "missing_diagnosis_made_other": qs.filter(tb_diagnosis=1, tb_diagnosis_made__value=96, diagnosis_made_other__isnull=True),
        "missing_tb_diagnosed_clinically": qs.filter(tb_diagnosis=1, tb_diagnosis_made=1)
            .annotate(clinical_count=Count("tb_diagnosed_clinically")).filter(clinical_count=0),
        "missing_tb_clinically_other": qs.filter(tb_diagnosis=1, tb_diagnosis_made=1, tb_diagnosed_clinically__value=96, tb_clinically_other__isnull=True).distinct(),
        "missing_bacteriological_diagnosis": qs.filter(tb_diagnosis=1, tb_diagnosis_made=2, bacteriological_diagnosis__isnull=True),
        "missing_clinician_received_date": qs.filter(tb_diagnosis=1, tb_diagnosis_made=2, clinician_received_date__isnull=True),
        "missing_tb_treatment_date": qs.filter(tb_treatment=1, tb_treatment_date__isnull=True),
        "missing_tb_register_number": qs.filter(tb_treatment=1, tb_register_number__isnull=True),
        "duplicate_tb_register_number": duplicate_tb_register_number_qs,
        "missing_tb_regimen": qs.filter(tb_treatment=1, tb_regimen__isnull=True),
        "missing_regimen_changed": qs.filter(tb_treatment=1, regimen_changed__isnull=True),
        "missing_tb_facility": qs.filter(tb_treatment=2, tb_facility__isnull=True),
        "missing_tb_reason": qs.filter(tb_treatment=96, tb_reason__isnull=True),
        "pending_tb_outcome": pending_tb_outcome_qs,
        "pending_tb_outcome_date": pending_tb_outcome_date_qs,
        "missing_tb_diagnosis_2_should_be_empty": missing_tb_diagnosis_2_should_be_empty,
        
        # DIAGNOSIS OTHER THAN TB
        "missing_tb_other_diagnosis": qs.filter(tb_diagnosis=2, tb_other_diagnosis__isnull=True),
        "missing_tb_diagnosis_made2": qs.filter(tb_diagnosis=2, tb_diagnosis_made2__isnull=True),
        "missing_tb_other_specify": qs.filter(tb_diagnosis=2, tb_other_diagnosis__value=96, tb_other_specify__isnull=True),
        "invalid_diag_other_than_tb_filled":invalid_diag_other_than_tb_filled,
        "invalid_mention_tb_other_specify_filled":invalid_mention_tb_other_specify_filled,
    }

    # ──────────────────────────────
    # Totals
    # ──────────────────────────────
    totals = {f"count_{k}": v.count() for k, v in problem_lists.items()}
    totals["diagnosis_report_total"] = sum(totals.values())

    return problem_lists, totals
