from django.views.generic import TemplateView

class QueriesDashboardView(TemplateView):
    template_name = "reports/data_quality/query_dashboard/queries_dashboard.html"
