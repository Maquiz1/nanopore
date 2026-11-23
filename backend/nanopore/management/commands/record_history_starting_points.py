from django.core.management.base import BaseCommand

from nanopore import history


class Command(BaseCommand):
    help = "Give every record without change history one starting entry (run once after the history migration)."

    def handle(self, *args, **options):
        created = history.record_starting_points()
        self.stdout.write(f"{created} starting entries recorded.")
