from django.core.management.base import BaseCommand
from django.apps import apps
from django.utils import timezone
from openpyxl import Workbook


class Command(BaseCommand):
    help = "Find screenings where zonal lab EXISTS but should NOT based on xpert logic"

    def handle(self, *args, **options):

        Screening = apps.get_model("nanopore", "Screening")

        today = timezone.localdate()

        screenings = Screening.objects.select_related(
            "site",
            "site__district__region__zone",
            "clinic_laboratory",
        )

        rows = []

        for s in screenings.iterator():

            # --- Get clinic laboratory safely ---
            clinic = getattr(s, "clinic_laboratory", None)
            if not clinic:
                continue

            xpert_mtb_id = getattr(getattr(clinic, "xpert_mtb", None), "id", None)
            rif_id = getattr(getattr(clinic, "xpert_mtb_rif_conducted", None), "id", None)

            # --- CONDITION WHERE ZONAL SHOULD NOT EXIST ---
            condition_met = xpert_mtb_id in [1, 7, 8, 9] or rif_id == 2
            if not condition_met:
                continue

            # --- Check if zonal laboratory exists (the actual problem) ---
            zonal = getattr(s, "zonal_laboratory", None)
            if not zonal:
                continue

            site = getattr(s, "site", None)
            zone = getattr(getattr(getattr(site, "district", None), "region", None), "zone", None)

            rows.append([
                s.id,
                getattr(s, "pid", ""),
                str(site) if site else "",
                str(zone) if zone else "",
                xpert_mtb_id,
                rif_id,
            ])

        # ---------------- Excel Export ----------------
        if rows:
            wb = Workbook()
            ws = wb.active
            ws.title = "Invalid Zonal Records"

            ws.append([
                "Screening ID",
                "PID",
                "Site",
                "Zone",
                "xpert_mtb_id",
                "xpert_mtb_rif_conducted_id",
            ])

            for r in rows:
                ws.append(r)

            filename = f"unexpected_zonal_{today}.xlsx"
            wb.save(filename)
            self.stdout.write(self.style.WARNING(f"Excel created: {filename}"))

        else:
            self.stdout.write(self.style.SUCCESS("No invalid zonal records found."))

        self.stdout.write(self.style.SUCCESS("Done."))
