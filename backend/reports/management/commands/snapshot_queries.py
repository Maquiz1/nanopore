import datetime

from django.core.management.base import BaseCommand

from reports.services.query_snapshot import take_snapshot


class Command(BaseCommand):
    help = "Save today's open query counts per site for the Query trends page (run daily)."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Label the counts with this date (YYYY-MM-DD) instead of today.")

    def handle(self, *args, **options):
        date = datetime.date.fromisoformat(options["date"]) if options["date"] else None
        run, rows = take_snapshot(date)
        self.stdout.write(self.style.SUCCESS(
            f"Query snapshot {run.snapshot_date}: {rows} count rows in {run.seconds}s"
        ))
