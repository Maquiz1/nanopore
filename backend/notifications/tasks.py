from celery import shared_task

from notifications import weekly


@shared_task
def send_weekly_query_emails():
    """Sunday night: open queries per site to the people who work on them."""
    return weekly.send_weekly_query_emails()


@shared_task
def send_weekly_outcome_emails():
    """Sunday night: Substudy 2 on treatment without an outcome, to staff of those zones/sites."""
    return weekly.send_weekly_outcome_emails()
