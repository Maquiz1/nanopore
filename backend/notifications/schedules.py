"""
Celery Beat jobs for the Sunday emails, kept in django-celery-beat's Periodic Tasks
(Django admin > Periodic Tasks) so admins can change the day/time or pause them there.

They are created once (migration 0002, or `manage.py setup_email_schedules`) and
never overwritten afterwards: an existing job keeps the schedule and on/off state
set in the admin. They are not in CELERY_BEAT_SCHEDULE, because beat rewrites
those from settings on every restart.
"""
import json

TIMEZONE = "Africa/Dar_es_Salaam"

# (name, task, default schedule: minute, hour, day_of_month, month_of_year, day_of_week, description)
SCHEDULES = [
    ("weekly_query_emails", "notifications.tasks.send_weekly_query_emails",
     ("0", "20", "*", "*", "0"), "Sunday 20:00: open queries per site to staff of their zones/sites"),
    ("weekly_treatment_outcome_emails", "notifications.tasks.send_weekly_outcome_emails",
     ("30", "20", "*", "*", "0"), "Sunday 20:30: Substudy 2 on treatment without an outcome"),
]


def ensure_schedules(PeriodicTask, CrontabSchedule):
    """Create missing jobs; existing ones only get their task path fixed. Returns [(name, created)]."""
    results = []
    for name, task_path, (minute, hour, dom, moy, dow), description in SCHEDULES:
        task = PeriodicTask.objects.filter(name=name).first()
        if task:
            if task.task != task_path:
                task.task = task_path
                task.save(update_fields=["task"])
            results.append((name, False))
            continue
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=minute, hour=hour, day_of_month=dom, month_of_year=moy, day_of_week=dow, timezone=TIMEZONE,
        )
        PeriodicTask.objects.create(name=name, task=task_path, crontab=crontab, kwargs=json.dumps({}),
                                    description=description, enabled=True)
        results.append((name, True))
    return results
