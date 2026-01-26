from django.views.generic import TemplateView


class SpecificFormQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/specific_form_queries_dashboard.html"