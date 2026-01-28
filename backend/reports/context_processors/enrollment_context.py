# reports/context_processors.py
from django.apps import apps
from utils.permissions import filter_queryset_by_user_role


def enrollment_report_total(request):
    """
    Navbar count for Enrollment data quality issues
    """

    if not request.user.is_authenticated:
        return {
            "enrollment_report_total": 0,

            # Basic
            "missing_enrollment_date": 0,
            "missing_cough2weeks": 0,
            "missing_poor_weight": 0,
            "missing_coughing_blood": 0,
            "missing_unexplained_fever": 0,
            "missing_night_sweats": 0,
            "missing_neck_lymph": 0,
            "missing_history_tb": 0,
            "missing_date_information_collected": 0,
            "missing_tx_previous": 0,

            # TB classification
            "missing_tb_category": 0,
            "missing_tb_category_specify": 0,
            "missing_dr_ds": 0,

            # Treatment
            "missing_tx_month": 0,
            "missing_tx_year": 0,
            "missing_tb_regimen": 0,
            "missing_tb_regimen_specify": 0,
            "missing_regimen_months": 0,

            # Outcomes
            "missing_tb_outcome": 0,
            "missing_ltf_months": 0,

            # Clinical
            "missing_hiv_status": 0,
            "missing_other_diseases": 0,
            "missing_sputum_collected": 0,
        }

    Enrollment = apps.get_model("nanopore", "Enrollment")

    # ── Role-based filtering ───────────────────────────────────────────────
    enrollments = Enrollment.objects.all()
    enrollments = filter_queryset_by_user_role(
        request.user,
        enrollments,
        site_field="screening__site"
    )

    # ───────────────────────────────────────────────────────────────────────
    # Missing fields
    # ───────────────────────────────────────────────────────────────────────

    missing_enrollment_date = enrollments.filter(enrollment_date__isnull=True).count()
    missing_cough2weeks = enrollments.filter(cough2weeks__isnull=True).count()
    missing_poor_weight = enrollments.filter(poor_weight__isnull=True).count()
    missing_coughing_blood = enrollments.filter(coughing_blood__isnull=True).count()
    missing_unexplained_fever = enrollments.filter(unexplained_fever__isnull=True).count()
    missing_night_sweats = enrollments.filter(night_sweats__isnull=True).count()
    missing_neck_lymph = enrollments.filter(neck_lymph__isnull=True).count()
    missing_history_tb = enrollments.filter(history_tb__isnull=True).count()
    missing_date_information_collected = enrollments.filter(
        date_information_collected__isnull=True
    ).count()
    missing_tx_previous = enrollments.filter(tx_previous__isnull=True).count()

    # TB classification
    missing_tb_category = enrollments.filter(tb_category__isnull=True).count()
    missing_tb_category_specify = enrollments.filter(tb_category_specify__isnull=True).count()
    missing_dr_ds = enrollments.filter(dr_ds__isnull=True).count()

    # Treatment
    missing_tx_month = enrollments.filter(tx_month__isnull=True).count()
    missing_tx_year = enrollments.filter(tx_year__isnull=True).count()
    missing_tb_regimen = enrollments.filter(tb_regimen__isnull=True).count()
    missing_tb_regimen_specify = enrollments.filter(
        tb_regimen_specify__isnull=True
    ).count()
    missing_regimen_months = enrollments.filter(regimen_months__isnull=True).count()

    # Outcomes
    missing_tb_outcome = enrollments.filter(tb_otcome__isnull=True).count()
    missing_ltf_months = enrollments.filter(ltf_months__isnull=True).count()

    # Clinical
    missing_hiv_status = enrollments.filter(hiv_status__isnull=True).count()
    missing_other_diseases = enrollments.filter(other_diseases__isnull=True).count()
    missing_sputum_collected = enrollments.filter(sputum_collected__isnull=True).count()

    # ───────────────────────────────────────────────────────────────────────
    # TOTAL ISSUES
    # ───────────────────────────────────────────────────────────────────────

    enrollment_report_total = (
        missing_enrollment_date
        + missing_cough2weeks
        + missing_poor_weight
        + missing_coughing_blood
        + missing_unexplained_fever
        + missing_night_sweats
        + missing_neck_lymph
        + missing_history_tb
        + missing_date_information_collected
        + missing_tx_previous
        + missing_tb_category
        + missing_tb_category_specify
        + missing_dr_ds
        + missing_tx_month
        + missing_tx_year
        + missing_tb_regimen
        + missing_tb_regimen_specify
        + missing_regimen_months
        + missing_tb_outcome
        + missing_ltf_months
        + missing_hiv_status
        + missing_other_diseases
        + missing_sputum_collected
    )

    return {
        "enrollment_report_total": enrollment_report_total,

        "missing_enrollment_date": missing_enrollment_date,
        "missing_cough2weeks": missing_cough2weeks,
        "missing_poor_weight": missing_poor_weight,
        "missing_coughing_blood": missing_coughing_blood,
        "missing_unexplained_fever": missing_unexplained_fever,
        "missing_night_sweats": missing_night_sweats,
        "missing_neck_lymph": missing_neck_lymph,
        "missing_history_tb": missing_history_tb,
        "missing_date_information_collected": missing_date_information_collected,
        "missing_tx_previous": missing_tx_previous,

        "missing_tb_category": missing_tb_category,
        "missing_tb_category_specify": missing_tb_category_specify,
        "missing_dr_ds": missing_dr_ds,

        "missing_tx_month": missing_tx_month,
        "missing_tx_year": missing_tx_year,
        "missing_tb_regimen": missing_tb_regimen,
        "missing_tb_regimen_specify": missing_tb_regimen_specify,
        "missing_regimen_months": missing_regimen_months,

        "missing_tb_outcome": missing_tb_outcome,
        "missing_ltf_months": missing_ltf_months,

        "missing_hiv_status": missing_hiv_status,
        "missing_other_diseases": missing_other_diseases,
        "missing_sputum_collected": missing_sputum_collected,
    }
