# reports/views.py
import io
import json
from django.shortcuts import render
from django.views import View
from django.db.models import Count
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

from nanopore.models import Screening, Enrollment, ClinicLaboratory, ZonalLaboratory, Diagnosis
from locations.models import Zone


# -----------------------
# Dashboard Report (charts)
# -----------------------
def dashboard_report(request):
    visits_per_site = {'Site A': 12, 'Site B': 19, 'Site C': 3, 'Site D': 5}
    mentorship_progress = [3, 7, 4, 6, 8, 10]
    competence_status = {'Completed': 10, 'Pending': 5, 'In Progress': 3}

    context = {
        'visits_labels': json.dumps(list(visits_per_site.keys())),
        'visits_data': json.dumps(list(visits_per_site.values())),
        'progress_labels': json.dumps(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']),
        'progress_data': json.dumps(mentorship_progress),
        'status_labels': json.dumps(list(competence_status.keys())),
        'status_data': json.dumps(list(competence_status.values())),
    }
    return render(request, 'reports/index.html', context)


# -----------------------
# Dashboard View
# -----------------------
class ReportDashboardView(View):
    template_name = "reports/dashboard.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


# -----------------------
# Summary Report
# -----------------------
from django.views import View
from django.shortcuts import render
from django.db.models import Count

from nanopore.models import Screening, Enrollment

class SummaryReportView(View):
    template_name = "reports/summary.html"

    def get(self, request, *args, **kwargs):
        # Count screenings and enrollments per site/zone
        data = (
            Screening.objects
            .values(
                "site__district__region__zone__name",
                "site__name"
            )
            .annotate(
                total_screenings=Count("id"),
                total_enrollments=Count("enrollment")  # assumes Enrollment has FK 'screening'
            )
            .order_by(
                "site__district__region__zone__name",
                "site__name"
            )
        )

        # Build zone totals + grand totals
        zone_totals = {}
        grand_totals = {"screenings": 0, "enrollments": 0}

        for row in data:
            zone_name = row["site__district__region__zone__name"]

            if zone_name not in zone_totals:
                zone_totals[zone_name] = {"screenings": 0, "enrollments": 0}

            zone_totals[zone_name]["screenings"] += row["total_screenings"]
            zone_totals[zone_name]["enrollments"] += row["total_enrollments"]

            grand_totals["screenings"] += row["total_screenings"]
            grand_totals["enrollments"] += row["total_enrollments"]

        return render(request, self.template_name, {
            "data": data,
            "zone_totals": zone_totals,
            "grand_totals": grand_totals,
        })



# -----------------------
# Forms Report
# -----------------------
class FormsReportView(View):
    template_name = "reports/forms.html"

    def get(self, request, *args, **kwargs):
        zones = Zone.objects.all()
        rows = []
        zone_totals = {}
        grand_totals = {
            "screenings": 0, "enrollments": 0,
            "clinic_lab": 0, "zonal_lab": 0, "diagnosis": 0,
        }

        for zone in zones:
            zone_totals[zone.name] = {
                "screenings": 0, "enrollments": 0,
                "clinic_lab": 0, "zonal_lab": 0, "diagnosis": 0,
            }

            # Get all sites under this zone
            sites = Screening.objects.filter(
                site__district__region__zone=zone
            ).values_list('site', flat=True).distinct()

            from locations.models import Site
            sites = Site.objects.filter(id__in=sites)

            for site in sites:
                row = {
                    "zone": zone.name,
                    "site": site.name,
                    "screenings": Screening.objects.filter(site=site).count(),
                    "enrollments": Enrollment.objects.filter(screening__site=site).count(),
                    "clinic_lab": ClinicLaboratory.objects.filter(screening__site=site).count(),
                    "zonal_lab": ZonalLaboratory.objects.filter(screening__site=site).count(),
                    "diagnosis": Diagnosis.objects.filter(screening__site=site).count(),
                }
                rows.append(row)

                # Add to zone totals
                for k in ["screenings", "enrollments", "clinic_lab", "zonal_lab", "diagnosis"]:
                    zone_totals[zone.name][k] += row[k]
                    grand_totals[k] += row[k]

        return render(request, self.template_name, {
            "rows": rows,
            "zone_totals": zone_totals,
            "grand_totals": grand_totals,
        })


# -----------------------
# Export Summary
# -----------------------
def export_summary(request, fmt):
    # Count screenings and enrollments per site/zone
    data = (
        Screening.objects
        .values(
            "site__district__region__zone__name",
            "site__name"
        )
        .annotate(
            total_screenings=Count("id"),
            total_enrollments=Count("enrollment")  # assumes Enrollment has FK 'screening'
        )
        .order_by(
            "site__district__region__zone__name",
            "site__name"
        )
    )

    # Prepare table data for Excel / PDF
    table_data = [["Zone", "Site", "Total Screenings", "Total Enrollments"]] + [
        [
            row["site__district__region__zone__name"],
            row["site__name"],
            row["total_screenings"],
            row["total_enrollments"],
        ]
        for row in data
    ]

    if fmt == "excel":
        wb = Workbook()
        ws = wb.active
        for r in table_data:
            ws.append(r)
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="summary.xlsx"'
        wb.save(response)
        return response

    elif fmt == "pdf":
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        style = getSampleStyleSheet()
        elements = [Paragraph("Summary Report – Screenings & Enrollments", style["Heading1"])]

        t = Table(table_data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t)
        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="summary.pdf"'
        response.write(pdf)
        return response



# -----------------------
# Export Forms
# -----------------------
def export_forms(request, fmt):
    table_data = [["Zone", "Site", "Screenings", "Enrollments", "Clinic Lab", "Zonal Lab", "Diagnosis"]]

    zones = Zone.objects.all()
    for zone in zones:
        # Get all sites under this zone
        sites = Screening.objects.filter(
            site__district__region__zone=zone
        ).values_list('site', flat=True).distinct()

        from locations.models import Site
        sites = Site.objects.filter(id__in=sites)

        for site in sites:
            table_data.append([
                zone.name,
                site.name,
                Screening.objects.filter(site=site).count(),
                Enrollment.objects.filter(screening__site=site).count(),
                ClinicLaboratory.objects.filter(screening__site=site).count(),
                ZonalLaboratory.objects.filter(screening__site=site).count(),
                Diagnosis.objects.filter(screening__site=site).count(),
            ])

    if fmt == "excel":
        wb = Workbook()
        ws = wb.active
        for r in table_data:
            ws.append(r)
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="forms.xlsx"'
        wb.save(response)
        return response

    elif fmt == "pdf":
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        style = getSampleStyleSheet()
        elements = [Paragraph("Forms Report", style["Heading1"])]

        t = Table(table_data)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t)
        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="forms.pdf"'
        response.write(pdf)
        return response
