from django.views.generic import TemplateView

class AllOverviewQueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/all_form_queries_overview_dashboard.html"
