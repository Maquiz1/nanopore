from django.views.generic import TemplateView

class MissingFormQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/missing_form_queries_dashboard.html"
