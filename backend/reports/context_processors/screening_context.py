from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from django.db.models import F, Q, Count
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def screening_report_total(request):
    """
    Returns screening data quality issues count for navbar.
    Includes missing fields, duplicates, mismatched PIDs, invalid lengths, and non-eligible cases.
    """
    screening_report_total = 0

    if not request.user.is_authenticated:
        return {"screening_report_total": screening_report_total}

    Screening = apps.get_model('nanopore', 'Screening')
    screenings = Screening.objects.all()
    screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

    # --- Data quality issues ---
    missing_fields_qs = screenings.filter(
        Q(pid1__isnull=True) | Q(pid2__isnull=True) |
        Q(sex__isnull=True) | Q(site__isnull=True) |
        Q(screening_date__isnull=True) |
        (Q(age__isnull=True) & Q(dob__isnull=True)) |
        Q(consent__isnull=True)
    )

    duplicate_pids = (
        screenings.values('pid')
        .annotate(pid_count=Count('id'))
        .filter(pid_count__gt=1)
    )
    duplicate_pid_list = [d['pid'] for d in duplicate_pids]
    duplicate_pid_qs = screenings.filter(pid__in=duplicate_pid_list)

    mismatched_pid_qs = screenings.filter(~Q(pid1=F('pid2')), pid1__isnull=False, pid2__isnull=False)
    invalid_length_qs = screenings.exclude(pid__isnull=True).exclude(pid__exact='').exclude(pid__regex=r'^.{16}$')
    not_eligible_qs = screenings.filter(eligible=False)

    # --- Total issues ---
    screening_report_total = (
        missing_fields_qs.count() +
        duplicate_pid_qs.count() +
        mismatched_pid_qs.count() +
        invalid_length_qs.count() +
        not_eligible_qs.count()
    )

    return {"screening_report_total": screening_report_total}
