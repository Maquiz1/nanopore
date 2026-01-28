from datetime import timedelta
from django.apps import apps
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from utils.permissions import filter_queryset_by_user_role


def diagnosis_report_total(request):
    """
    Navbar count for Diagnosis issues.

    Includes:
    1) Diagnosis records with missing required fields
    2) TB patients started on treatment ≥ 6 months ago
       but missing outcome or outcome date
    """

    diagnosis_total = 0

    if not request.user.is_authenticated:
        return {"diagnosis_report_total": diagnosis_total}

    # --------------------------------------------------
    # Models
    # --------------------------------------------------
    Diagnosis = apps.get_model("nanopore", "Diagnosis")
    Screening = apps.get_model("nanopore", "Screening")

    # --------------------------------------------------
    # Diagnosis forms
    # --------------------------------------------------
    diagnoses = Diagnosis.objects.all()
    diagnoses = filter_queryset_by_user_role(
        request.user,
        diagnoses,
        site_field="screening__site"
    )

    # --------------------------------------------------
    # Required diagnosis completeness fields
    # --------------------------------------------------
    # required_fields = [
        # "tb_diagnosis",
        # "tb_diagnosis_date",
        # "tb_diagnosis_made",
        # "bacteriological_diagnosis",
        # "tb_treatment",
        # "tb_treatment_date",
        # "tb_facility",
        # "tb_regimen",
        # "tb_outcome2",
    # ]

    # --------------------------------------------------
    # 1️⃣ Incomplete diagnosis forms
    # --------------------------------------------------
    incomplete_diagnosis_forms = 0

    # for d in diagnoses:
    #     for field in required_fields:

    #         try:
    #             value = getattr(d, field)
    #         except ObjectDoesNotExist:
    #             # FK exists in model but related row missing in DB
    #             value = None

    #         if value in (None, "", False):
    #             incomplete_diagnosis_forms += 1
    #             break  # count once per diagnosis

    # diagnosis_total += incomplete_diagnosis_forms

    # # --------------------------------------------------
    # # 2️⃣ Clinical workflow checks (TB outcomes)
    # # --------------------------------------------------
    # screenings = Screening.objects.all()
    # screenings = filter_queryset_by_user_role(
    #     request.user,
    #     screenings,
    #     site_field="site"
    # )

    # six_months_ago = timezone.now().date() - timedelta(days=180)

    # treatment_started_6m_ago = screenings.filter(
    #     diagnosis__tb_treatment=1,
    #     diagnosis__tb_treatment_date__isnull=False,
    #     diagnosis__tb_treatment_date__lte=six_months_ago
    # )

    # pending_tb_outcomes = treatment_started_6m_ago.filter(
    #     diagnosis__tb_outcome2__isnull=True
    # )

    # pending_tb_outcomes_date = treatment_started_6m_ago.filter(
    #     diagnosis__tb_outcome2_date__isnull=True
    # )

    # diagnosis_total += (
    #     pending_tb_outcomes.count()
    #     + pending_tb_outcomes_date.count()
    # )

    return {
        "diagnosis_report_total": diagnosis_total
    }
