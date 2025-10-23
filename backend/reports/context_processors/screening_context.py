from django.utils import timezone
from django.apps import apps
from django.db.models import F, Q, Count
from utils.permissions import filter_queryset_by_user_role


def screening_report_total(request):
    """
    Returns screening data quality issues count for navbar.
    Includes missing fields, duplicates, mismatched PIDs, invalid lengths, non-eligible cases,
    and missing produce_resp_sample or genexpert_confirmation.
    """
    if not request.user.is_authenticated:
        return {"screening_report_total": 0}

    Screening = apps.get_model('nanopore', 'Screening')
    screenings = Screening.objects.all()
    screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

    # --- Individual Missing Fields ---
    missing_screening_date = screenings.filter(screening_date__isnull=True).count()
    missing_pid1 = screenings.filter(pid1__isnull=True).count()
    missing_pid2 = screenings.filter(pid2__isnull=True).count()
    missing_sex = screenings.filter(sex__isnull=True).count()
    missing_age_or_dob = screenings.filter(age__isnull=True, dob__isnull=True).count()
    missing_consent = screenings.filter(consent__isnull=True).count()
    missing_age18years = screenings.filter(age18years__isnull=True).count()
    missing_present_symptoms = screenings.filter(present_symptoms__isnull=True).count()
    missing_produce_resp_sample = screenings.filter(produce_resp_sample__isnull=True).count()
    missing_genexpert_confirmation = screenings.filter(genexpert_confirmation__isnull=True).count()
    missing_unable_understand = screenings.filter(unable_understand__isnull=True).count()
    missing_not_willing = screenings.filter(not_willing__isnull=True).count()
    missing_enrolled = screenings.filter(enrolled__isnull=True).count()
    missing_reasons = screenings.filter(reasons__isnull=True, enrolled__name__iexact="yes").count()

    # --- PID Issues ---
    duplicate_pids = (
        screenings.values('pid').annotate(pid_count=Count('id')).filter(pid_count__gt=1)
    )
    duplicate_pid_count = duplicate_pids.count()
    
    mismatched_pid_count = screenings.filter(~Q(pid1=F('pid2')), pid1__isnull=False, pid2__isnull=False).count()
    invalid_length_pid_count = screenings.exclude(pid__isnull=True).exclude(pid__exact='').exclude(pid__regex=r'^.{16}$').count()
    
    # --- Not Eligible ---
    not_eligible_count = screenings.filter(eligible=False).count()

    # --- Total ---
    screening_report_total = (
        missing_screening_date +
        missing_pid1 +
        missing_pid2 +
        missing_sex +
        missing_age_or_dob +
        missing_consent +
        missing_age18years +
        missing_present_symptoms +
        missing_produce_resp_sample +
        missing_genexpert_confirmation +
        missing_unable_understand +
        missing_not_willing +
        missing_enrolled +
        missing_reasons +
        duplicate_pid_count +
        mismatched_pid_count +
        invalid_length_pid_count +
        not_eligible_count
    )

    return {"screening_report_total": screening_report_total}
