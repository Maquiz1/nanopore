from celery import shared_task

from notifications import weekly


@shared_task
def send_weekly_query_emails():
    """Sunday night: open queries per site to the people who work on them."""
    from nanopore import study_lock
    if not study_lock.job_allowed("Weekly emails"):
        return "Skipped: the study is locked"
    return weekly.send_weekly_query_emails()


@shared_task
def send_weekly_outcome_emails():
    """Sunday night: Substudy 2 on treatment without an outcome, to staff of those zones/sites."""
    from nanopore import study_lock
    if not study_lock.job_allowed("Weekly emails"):
        return "Skipped: the study is locked"
    return weekly.send_weekly_outcome_emails()
