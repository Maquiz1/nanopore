# reports/views/exports.py
import csv
from django.http import HttpResponse
from django.views import View
from nanopore.models import Screening

from datetime import date
from dateutil.relativedelta import relativedelta

def annotate_months_and_substudy_for_export(qs, months_filter=None, substudy_filter=None):
    annotated_qs = []
    for obj in qs:
        # Months since TB treatment
        if obj.tb_treatment_date:
            delta = relativedelta(date.today(), obj.tb_treatment_date)
            obj.months_since_treatment = delta.years * 12 + delta.months
        else:
            obj.months_since_treatment = None

        # Determine Substudy
        lab = getattr(obj.screening, "clinic_laboratory", None)
        if lab and lab.xpert_mtb:
            xpert_id = lab.xpert_mtb.id if hasattr(lab.xpert_mtb, 'id') else lab.xpert_mtb
            if xpert_id in [2,3,4,5,6]:
                obj.substudy = "Substudy 2"
            elif xpert_id in [1,7,8,9]:
                obj.substudy = "Substudy 4"
            else:
                obj.substudy = "Uncategorized"
        else:
            obj.substudy = "Uncategorized"

        # Apply filters
        if months_filter and (obj.months_since_treatment is None or obj.months_since_treatment < months_filter):
            continue
        if substudy_filter and obj.substudy != substudy_filter:
            continue

        annotated_qs.append(obj)
    return annotated_qs


class ScreeningCsvExportView(View):
    """Export Screenings to CSV with optional filters"""
    def get(self, request, *args, **kwargs):
        qs = Screening.objects.select_related("site__district__region__zone")

        # Filters from GET params
        zone_id = request.GET.get("zone")
        site_id = request.GET.get("site")
        months_filter = request.GET.get("months")
        months_filter = int(months_filter) if months_filter else None
        substudy_filter = request.GET.get("substudy")

        if zone_id:
            qs = qs.filter(site__district__region__zone_id=zone_id)
        if site_id:
            qs = qs.filter(site_id=site_id)

        qs = annotate_months_and_substudy_for_export(qs, months_filter, substudy_filter)

        # CSV Response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="screenings.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "PID", "PID1", "PID2", "Site", "Zone", "TB Outcome",
            "TB Treatment Date", "Months Since Treatment", "Substudy"
        ])

        for s in qs:
            writer.writerow([
                s.pid,
                s.pid1,
                s.pid2,
                s.site.name if s.site else "",
                s.site.district.region.zone.name if s.site and s.site.district and s.site.district.region and s.site.district.region.zone else "",
                getattr(s, "tb_outcome2", ""),
                getattr(s, "tb_treatment_date", ""),
                getattr(s, "months_since_treatment", ""),
                getattr(s, "substudy", ""),
            ])

        return response
