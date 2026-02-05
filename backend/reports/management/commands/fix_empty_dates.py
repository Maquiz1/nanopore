from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction

class Command(BaseCommand):
    help = "Replace empty string dates with NULL in all DateFields in the Screening model"

    def handle(self, *args, **options):
        # Replace 'nanopore.Screening' with your actual app.model
        Screening = apps.get_model("nanopore", "Screening")
        date_fields = [
            f.name for f in Screening._meta.get_fields()
            if f.get_internal_type() == "DateField"
        ]

        self.stdout.write(f"Found date fields: {date_fields}")

        total_updated = 0

        with transaction.atomic():
            for field in date_fields:
                # Filter rows where date field is empty string
                qs = Screening.objects.filter(**{f"{field}": ""})
                count = qs.count()
                if count > 0:
                    qs.update(**{field: None})
                    total_updated += count
                    self.stdout.write(f"Updated {count} records: {field}")

        self.stdout.write(self.style.SUCCESS(f"Done! Total records updated: {total_updated}"))
