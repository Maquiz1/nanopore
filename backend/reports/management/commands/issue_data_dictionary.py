from django.core.management.base import BaseCommand, CommandError

from reports import data_dictionary


class Command(BaseCommand):
    help = "Write the current data dictionary version from the previous one (reports/data_dictionary.py)."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True, help="The previous version's .xlsx")
        parser.add_argument("--as-version", help="Keep the source exactly as received, as this version (e.g. 0.1)")

    def handle(self, *args, **options):
        try:
            if options["as_version"]:
                path = data_dictionary.keep_as_issued(options["source"], options["as_version"])
                self.stdout.write(f"Kept as issued: {path}")
                return
            path, changed = data_dictionary.issue(options["source"])
        except (OSError, ValueError, KeyError) as exc:
            raise CommandError(str(exc))
        self.stdout.write(f"Wrote {path} ({changed} cells changed).")
