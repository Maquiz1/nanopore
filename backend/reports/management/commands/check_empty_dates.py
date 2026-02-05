# reports/management/commands/check_empty_dates.py

from django.core.management.base import BaseCommand
from django.apps import apps
from openpyxl import Workbook
from pathlib import Path


class Command(BaseCommand):
    help = "Export ZonalLaboratory records with empty ('') or NULL date fields to Excel"

    def handle(self, *args, **options):
        ZonalLaboratory = apps.get_model("nanopore", "ZonalLaboratory")

        # Collect all DateFields
        date_fields = [
            f.name for f in ZonalLaboratory._meta.get_fields()
            if f.get_internal_type() == "DateField"
        ]

        self.stdout.write(f"Checking date fields: {date_fields}\n")

        qs = ZonalLaboratory.objects.all().values("id", *date_fields, "screening__pid")

        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Empty Dates"

        # Header
        ws.append(["ID", "PID", "Field", "Value"])

        rows_written = 0

        for obj in qs:
            pid = obj.get("screening__pid") or "N/A"

            for field in date_fields:
                value = obj.get(field)

                if value in (None, ""):
                    ws.append([
                        obj["id"],
                        pid,
                        field,
                        "" if value == "" else "NULL",
                    ])
                    rows_written += 1

        # Save file
        output_path = Path("empty_zonal_dates.xlsx")
        wb.save(output_path)

        self.stdout.write(self.style.SUCCESS(
            f"Done. {rows_written} rows written to {output_path.resolve()}"
        ))
