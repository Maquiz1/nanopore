from django.views.generic import TemplateView

class QueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/queries_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        request = self.request
        context["forms_total"] = getattr(request, "context", {}).get("forms_report_total", 0)
        context["screening_total"] = getattr(request, "context", {}).get("screening_report_total", 0)
        context["enrollment_total"] = getattr(request, "context", {}).get("enrollment_report_total", 0)
        context["clinic_total"] = getattr(request, "context", {}).get("clinic_report_total", 0)
        context["diagnosis_total"] = getattr(request, "context", {}).get("diagnosis_report_total", 0)
        context["regimen_total"] = getattr(request, "context", {}).get("regimen_report_total", 0)
        context["zonal_total"] = getattr(request, "context", {}).get("zonal_report_total", 0)

        context["total_issues"] = (
            context["forms_total"]
            + context["screening_total"]
            + context["enrollment_total"]
            + context["clinic_total"]
            + context["diagnosis_total"]
            + context["regimen_total"]
            + context["zonal_total"]
        )

        return context
