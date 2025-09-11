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
from nanopore.models import Enrollment, Diagnosis, ClinicLaboratory
from django.views.generic import TemplateView
from django.db.models import Count, Q
from nanopore.models import Enrollment, Diagnosis, ClinicLaboratory

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




from django.views.generic import TemplateView
from django.db.models import Count, Q
from nanopore.models import Enrollment, Diagnosis, ClinicLaboratory

class EnrollmentSummaryView(TemplateView):
    template_name = "reports/enrollment_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Base Query ---
        enrollments = Enrollment.objects.select_related(
            "screening__site__district__region__zone"
        )
        diagnoses = Diagnosis.objects.select_related(
            "screening__site__district__region__zone"
        )
        labs = ClinicLaboratory.objects.select_related(
            "screening__site__district__region__zone"
        )

        # --- Filters (optional from request) ---
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if zone_id:
            enrollments = enrollments.filter(screening__site__district__region__zone_id=zone_id)
            diagnoses = diagnoses.filter(screening__site__district__region__zone_id=zone_id)
            labs = labs.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            enrollments = enrollments.filter(screening__site_id=site_id)
            diagnoses = diagnoses.filter(screening__site_id=site_id)
            labs = labs.filter(screening__site_id=site_id)
        if start_date and end_date:
            enrollments = enrollments.filter(screening__screening_date__range=[start_date, end_date])
            diagnoses = diagnoses.filter(screening__screening_date__range=[start_date, end_date])
            labs = labs.filter(screening__screening_date__range=[start_date, end_date])

        # --- Aggregations ---
        total_enrolled = enrollments.count()
        substudy2_count = labs.filter(xpert_mtb__in=[2, 3, 4, 5, 6]).count()
        substudy4_count = labs.filter(xpert_mtb__in=[1, 7, 8, 9]).count()

        # By Zone
        zone_summary = (
            enrollments.values("screening__site__district__region__zone__name")
            .annotate(
                enrolled=Count("id", distinct=True),
                substudy2=Count(
                    "screening__clinic_laboratory",
                    filter=Q(screening__clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6]),
                    distinct=True,
                ),
                substudy4=Count(
                    "screening__clinic_laboratory",
                    filter=Q(screening__clinic_laboratory__xpert_mtb__in=[1, 7, 8, 9]),
                    distinct=True,
                ),
            )
            .order_by("screening__site__district__region__zone__name")
        )
        
        
        # By Site
        site_summary = (
            enrollments.values(
                "screening__site__district__region__zone__name",
                "screening__site__name"
            )
            .annotate(
                enrolled=Count("id", distinct=True),
                                            substudy2=Count(
                    "screening__clinic_laboratory",
                    filter=Q(screening__clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6]),
                    distinct=True,
                                                    ),
                substudy4=Count(
                    "screening__clinic_laboratory",
                    filter=Q(screening__clinic_laboratory__xpert_mtb__in=[1, 7, 8, 9]),
                    distinct=True,
                ),
            )
            .order_by("screening__site__district__region__zone__name", "screening__site__name")
        )       

        context.update({
            "total_enrolled": total_enrolled,
            "substudy2_count": substudy2_count,
            "substudy4_count": substudy4_count,
            "zone_summary": zone_summary,
            "site_summary": site_summary,
        })
                

        context.update(
            {
                "total_enrolled": total_enrolled,
                "substudy2_count": substudy2_count,
                "substudy4_count": substudy4_count,
                "zone_summary": zone_summary,
            }
        )
        return context
    
    
    
class CompletedStudySummaryView(TemplateView):
    template_name = "reports/completed_study_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        diagnoses = Diagnosis.objects.select_related(
            "screening__site__district__region__zone"
        )

        # --- Filters (optional from request) ---
        zone_id = self.request.GET.get("zone")
        site_id = self.request.GET.get("site")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if zone_id:
            diagnoses = diagnoses.filter(screening__site__district__region__zone_id=zone_id)
        if site_id:
            diagnoses = diagnoses.filter(screening__site_id=site_id)
        if start_date and end_date:
            diagnoses = diagnoses.filter(screening__screening_date__range=[start_date, end_date])

        # --- Aggregation by Zone ---
        zone_summary = (
            diagnoses.values("screening__site__district__region__zone__name")
            .annotate(
                completed=Count(
                    "id",
                    filter=Q(tb_outcome2__in=[1, 2]) & ~Q(tb_outcome2__isnull=True),
                ),
                in_progress=Count(
                    "id",
                    filter=~Q(tb_outcome2__in=[1, 2]) | Q(tb_outcome2__isnull=True),
                ),
            )
            .order_by("screening__site__district__region__zone__name")
        )

        # --- Totals ---
        total_completed = diagnoses.filter(tb_outcome2__in=[1, 2]).exclude(tb_outcome2__isnull=True).count()
        total_in_progress = diagnoses.exclude(tb_outcome2__in=[1, 2]).count()


        # By Site
        site_summary = (
            diagnoses.values(
                "screening__site__district__region__zone__name",
                "screening__site__name"
            )
            .annotate(
                completed=Count(
                    "id",
                    filter=Q(tb_outcome2__in=[1, 2]) & ~Q(tb_outcome2__isnull=True),
                ),
                in_progress=Count(
                    "id",
                    filter=~Q(tb_outcome2__in=[1, 2]) | Q(tb_outcome2__isnull=True),
                ),
            )
            .order_by("screening__site__district__region__zone__name", "screening__site__name")
        )

        context.update(
            {
                "zone_summary": zone_summary,
                "site_summary": site_summary,
                "total_completed": total_completed,
                "total_in_progress": total_in_progress,
            }
        )
        return context
