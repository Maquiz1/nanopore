from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from notifications.schedules import ensure_schedules


class Command(BaseCommand):
    help = ("Create the Celery Beat jobs for the Sunday emails if they are missing. "
            "Existing jobs keep the schedule and on/off state set in Django admin > Periodic Tasks.")

    def handle(self, *args, **options):
        for name, created in ensure_schedules(PeriodicTask, CrontabSchedule):
            task = PeriodicTask.objects.select_related("crontab").get(name=name)
            state = "Created" if created else "Kept"
            self.stdout.write(f"{state}: {name} -> {task.crontab} ({'on' if task.enabled else 'paused'})")
