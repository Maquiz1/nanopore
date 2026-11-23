from django.core.management.base import BaseCommand, CommandError

from reports import data_dictionary


class Command(BaseCommand):
    help = "Keep or correct the study team's data dictionary, or save the current one (reports/data_dictionary.py)."

    def add_arguments(self, parser):
        parser.add_argument("--source", help="The study team's .xlsx to correct (v0.2) or keep as received (--as-version)")
        parser.add_argument("--current", action="store_true", help="Save the current version, built from the system, as a file")
        parser.add_argument("--as-version", help="Keep the source exactly as received, as this version (e.g. 0.1)")

    def handle(self, *args, **options):
        try:
            if options["current"]:
                self.stdout.write(f"Wrote {data_dictionary.write_current()}")
                return
            if not options["source"]:
                raise CommandError("--source is needed (or --current).")
            if options["as_version"]:
                path = data_dictionary.keep_as_issued(options["source"], options["as_version"])
                self.stdout.write(f"Kept as issued: {path}")
                return
            path, changed = data_dictionary.issue(options["source"])
        except (OSError, ValueError, KeyError) as exc:
            raise CommandError(str(exc))
        self.stdout.write(f"Wrote {path} ({changed} cells changed).")
